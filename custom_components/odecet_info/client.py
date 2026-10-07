"""HTTP client for odecet.info.

The session is injected. Home Assistant passes a dedicated client so the
login cookies stay off the shared session, and tests pass a fake. This
module does not import Home Assistant.
"""

from __future__ import annotations

import asyncio
import re
from datetime import date, datetime
from urllib.parse import urljoin, urlsplit
from zoneinfo import ZoneInfo

import aiohttp

from custom_components.odecet_info.errors import (
    OdecetAuthError,
    OdecetError,
    OdecetRateLimitError,
    OdecetStructureError,
    OdecetTransportError,
    OdecetValidationError,
)
from custom_components.odecet_info.html_extract import (
    HtmlForm,
    SelectField,
    is_sign_in_page,
    parse_page,
)
from custom_components.odecet_info.models import FetchMethod, ReadingIssue, ReadingSet
from custom_components.odecet_info.parse import (
    history_as_csv,
    parse_csv,
    parse_history_html,
)

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
SITE_TIMEZONE = ZoneInfo("Europe/Prague")
REQUEST_TIMEOUT_SECONDS = 60


class OdecetClient:
    """Sign in and return a normalized reading set."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        signin_url: str,
        username: str,
        password: str,
    ) -> None:
        self._session = session
        self._signin_url = signin_url
        self._username = username.strip()
        self._password = password
        self._signed_in = False
        parts = urlsplit(signin_url)
        self._origin = f"{parts.scheme}://{parts.netloc}"

    async def async_login(self) -> None:
        """Load the form, then post credentials. Raises before the POST when invalid."""
        self._reject_local_input()
        html, status = await self._request("GET", self._signin_url)
        self._raise_for_status(status)
        if is_sign_in_page(html) is False and "__RequestVerificationToken" not in html:
            raise OdecetStructureError("Sign-in page was not recognized")
        token = _find_token(html)
        if not token:
            raise OdecetStructureError("Sign-in page has no antiforgery token")
        action = urljoin(self._signin_url, _find_sign_in_action(html) or self._signin_url)
        # `website` is the honeypot. It must be present and empty.
        body, status = await self._request(
            "POST",
            action,
            form={
                "email": self._username,
                "password": self._password,
                "__RequestVerificationToken": token,
                "website": "",
            },
        )
        self._raise_for_status(status)
        if body.strip() != "True":
            raise OdecetAuthError("Sign-in was rejected")
        self._signed_in = True

    async def async_fetch(
        self,
        method: FetchMethod,
        sync_from: date | None = None,
        *,
        now: datetime | None = None,
    ) -> ReadingSet:
        """Return readings for the chosen method, filtered to `sync_from`."""
        if not self._signed_in:
            await self.async_login()
        dashboard = await self._load_dashboard(sync_from, now)
        if is_sign_in_page(dashboard):
            raise OdecetAuthError("Session expired before the dashboard loaded")
        parsed = await self._parse_dashboard(dashboard, method, now)
        return _filter_from(parsed, sync_from)

    async def _load_dashboard(self, sync_from: date | None, now: datetime | None) -> str:
        html, status = await self._request("GET", f"{self._origin}/")
        self._raise_for_status(status)
        if is_sign_in_page(html):
            raise OdecetAuthError("Session expired before the dashboard loaded")
        form = _find_period_form(html)
        if form is None:
            return html
        current = (now or datetime.now(SITE_TIMEZONE)).astimezone(SITE_TIMEZONE).date()
        start = sync_from or _earliest_period(form) or current
        params = _period_params(form, start, current)
        ranged, ranged_status = await self._request("GET", f"{self._origin}/", params=params)
        self._raise_for_status(ranged_status)
        return ranged

    async def _parse_dashboard(
        self,
        dashboard: str,
        method: FetchMethod,
        now: datetime | None,
    ) -> ReadingSet:
        if method is FetchMethod.TABLE:
            return parse_history_html(dashboard, now=now)
        try:
            csv_text = await self._csv_document(dashboard)
            return parse_csv(csv_text, now=now)
        except OdecetError:
            if method is FetchMethod.CSV:
                raise
            return parse_history_html(dashboard, now=now)

    async def _csv_document(self, dashboard: str) -> str:
        link = _find_csv_link(dashboard)
        if link:
            body, status = await self._request("GET", urljoin(self._origin, link))
            self._raise_for_status(status)
            if is_sign_in_page(body):
                raise OdecetAuthError("CSV export returned the sign-in page")
            return body
        return history_as_csv(dashboard)

    def _reject_local_input(self) -> None:
        if not self._password:
            raise OdecetValidationError("Password is required")
        if EMAIL_PATTERN.match(self._username) is None:
            raise OdecetValidationError("Username must be an email address")

    async def _request(
        self,
        method: str,
        url: str,
        *,
        form: dict[str, str] | None = None,
        params: dict[str, str] | None = None,
    ) -> tuple[str, int]:
        try:
            async with asyncio.timeout(REQUEST_TIMEOUT_SECONDS):
                if method == "GET":
                    context = self._session.get(url, params=params)
                else:
                    payload = aiohttp.FormData()
                    for name, value in (form or {}).items():
                        payload.add_field(name, value)
                    context = self._session.post(url, data=payload)
                async with context as response:
                    body = await response.text(errors="replace")
                    return body, response.status
        except TimeoutError as err:
            raise OdecetTransportError("The request to odecet.info timed out") from err
        except aiohttp.ClientError as err:
            raise OdecetTransportError("The request to odecet.info failed") from err

    @staticmethod
    def _raise_for_status(status: int) -> None:
        if status == 429:
            raise OdecetRateLimitError("odecet.info rate limited the request")
        if status >= 500:
            raise OdecetTransportError(f"odecet.info returned HTTP {status}")
        if status >= 400:
            raise OdecetTransportError(f"odecet.info returned HTTP {status}")


def _find_token(html: str) -> str | None:
    forms, _tables = parse_page(html)
    for form in forms:
        for field in form.fields:
            if field.name == "__RequestVerificationToken" and field.value:
                return field.value
    return None


def _find_sign_in_action(html: str) -> str | None:
    forms, _tables = parse_page(html)
    for form in forms:
        if any(field.name == "__RequestVerificationToken" for field in form.fields):
            return form.action
    return None


def _find_period_form(html: str) -> HtmlForm | None:
    forms, _tables = parse_page(html)
    for form in forms:
        names = {field.name for field in form.fields}
        selects = {select.name for select in form.selects}
        period = {"fromMonth", "fromYear", "toMonth", "toYear"}
        if "flat" in names and period <= selects:
            return form
    return None


def _earliest_period(form: HtmlForm) -> date | None:
    years = _select(form, "fromYear")
    if years is None or not years.options:
        return None
    numeric = [int(option) for option in years.options if option.isdigit()]
    if not numeric:
        return None
    return date(min(numeric), 1, 1)


def _period_params(form: HtmlForm, start: date, end: date) -> dict[str, str]:
    """Month range covered by the form, clamped to the options the page offers."""
    from_years = _numeric_options(form, "fromYear")
    to_years = _numeric_options(form, "toYear")
    start_year = _clamp(start.year, from_years) if from_years else start.year
    end_year = _clamp(end.year, to_years) if to_years else end.year
    params = {
        "fromMonth": str(start.month if start.year == start_year else 1),
        "fromYear": str(start_year),
        "toMonth": str(end.month if end.year == end_year else 12),
        "toYear": str(end_year),
    }
    for field in form.fields:
        if field.field_type == "hidden" and field.name:
            params[field.name] = field.value
    return params


def _select(form: HtmlForm, name: str) -> SelectField | None:
    for select in form.selects:
        if select.name == name:
            return select
    return None


def _numeric_options(form: HtmlForm, name: str) -> list[int]:
    select = _select(form, name)
    if select is None:
        return []
    return [int(option) for option in select.options if option.isdigit()]


def _clamp(value: int, options: list[int]) -> int:
    if value < min(options):
        return min(options)
    if value > max(options):
        return max(options)
    return value


def _find_csv_link(html: str) -> str | None:
    match = re.search(r'href="([^"]+\.csv(?:\?[^"]*)?)"', html, flags=re.IGNORECASE)
    if match is None:
        return None
    link = match.group(1)
    if link.startswith("#") or link.lower().startswith("javascript:"):
        return None
    return link


def _filter_from(parsed: ReadingSet, sync_from: date | None) -> ReadingSet:
    if sync_from is None:
        return parsed
    kept = tuple(reading for reading in parsed.readings if reading.timestamp.date() >= sync_from)
    ignored = len(parsed.readings) - len(kept)
    issues = parsed.issues
    if ignored:
        issues = issues + (
            ReadingIssue(
                "before_sync_from",
                f"{ignored} readings were before the sync start date",
            ),
        )
    return ReadingSet(kept, issues, parsed.source)
