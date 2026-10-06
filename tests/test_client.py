"""Client tests. The session is scripted and does not contact odecet.info."""

from datetime import date, datetime
from zoneinfo import ZoneInfo

import pytest
from custom_components.odecet_info.client import OdecetClient
from custom_components.odecet_info.errors import (
    OdecetAuthError,
    OdecetRateLimitError,
    OdecetStructureError,
    OdecetTransportError,
    OdecetValidationError,
)
from custom_components.odecet_info.models import FetchMethod, Medium
from tests.fakes import Response, ScriptedSession, form_fields, load_fixture

PRAGUE = ZoneInfo("Europe/Prague")
NOW = datetime(2026, 10, 6, 12, tzinfo=PRAGUE)
SIGNIN = "https://odecet.info/signin"


def _session(*bodies: tuple[int, str] | Exception) -> ScriptedSession:
    responses: list[Response | Exception] = []
    for item in bodies:
        if isinstance(item, Exception):
            responses.append(item)
        else:
            status, body = item
            responses.append(Response(status, body, SIGNIN))
    return ScriptedSession(responses)


def _client(session: ScriptedSession, password: str = "secret-value") -> OdecetClient:
    return OdecetClient(session, SIGNIN, "user@example.com", password)


@pytest.mark.asyncio
async def test_login_posts_token_and_empty_honeypot() -> None:
    session = _session(
        (200, load_fixture("signin.html")),
        (200, "True"),
        (200, load_fixture("dashboard.html")),
        (200, load_fixture("dashboard.html")),
    )
    parsed = await _client(session).async_fetch(FetchMethod.TABLE, now=NOW)
    post = session.calls[1]
    fields = form_fields(post["data"])
    assert fields["email"] == "user@example.com"
    assert fields["password"] == "secret-value"
    assert fields["__RequestVerificationToken"] == "token-value"
    assert fields["website"] == ""
    assert post["url"] == SIGNIN
    ranged = session.calls[3]
    assert ranged["params"]["flat"] == "FLAT-1"
    assert ranged["params"]["fromYear"] == "2024"
    assert {meter.medium for meter in parsed.meters()} == set(Medium)


@pytest.mark.asyncio
async def test_csv_and_table_modes_both_return_meters() -> None:
    pages = (
        (200, load_fixture("signin.html")),
        (200, "True"),
        (200, load_fixture("dashboard.html")),
        (200, load_fixture("dashboard.html")),
    )
    table = await _client(_session(*pages)).async_fetch(FetchMethod.TABLE, now=NOW)
    csv_parsed = await _client(_session(*pages)).async_fetch(FetchMethod.CSV, now=NOW)
    auto = await _client(_session(*pages)).async_fetch(FetchMethod.AUTO, now=NOW)
    assert table.source == "table"
    assert csv_parsed.source == "csv"
    assert auto.source == "csv"
    assert len(table.meters()) == len(csv_parsed.meters()) == len(auto.meters())


@pytest.mark.asyncio
async def test_sync_from_drops_older_readings() -> None:
    session = _session(
        (200, load_fixture("signin.html")),
        (200, "True"),
        (200, load_fixture("dashboard.html")),
        (200, load_fixture("dashboard.html")),
    )
    parsed = await _client(session).async_fetch(
        FetchMethod.TABLE,
        sync_from=date(2026, 1, 1),
        now=NOW,
    )
    cold = next(meter for meter in parsed.meters() if meter.serial == "1001")
    assert all(reading.timestamp.date() >= date(2026, 1, 1) for reading in cold.readings)
    assert any(issue.code == "before_sync_from" for issue in parsed.issues)
    assert session.calls[3]["params"]["fromYear"] == "2026"
    assert session.calls[3]["params"]["fromMonth"] == "1"


@pytest.mark.asyncio
async def test_bad_password_is_auth_and_does_not_leak() -> None:
    session = _session((200, load_fixture("signin.html")), (200, "False"))
    with pytest.raises(OdecetAuthError) as caught:
        await _client(session).async_login()
    assert "secret-value" not in str(caught.value)


@pytest.mark.asyncio
async def test_empty_password_is_rejected_locally() -> None:
    session = _session()
    with pytest.raises(OdecetValidationError):
        await _client(session, password="").async_login()
    assert session.calls == []


@pytest.mark.asyncio
async def test_invalid_email_is_rejected_locally() -> None:
    session = _session()
    client = OdecetClient(session, SIGNIN, "not-an-email", "secret-value")
    with pytest.raises(OdecetValidationError):
        await client.async_login()
    assert session.calls == []


@pytest.mark.asyncio
async def test_missing_token_is_a_structure_error() -> None:
    session = _session((200, "<html><form id='kt_sign_in_form'></form></html>"))
    with pytest.raises(OdecetStructureError):
        await _client(session).async_login()


@pytest.mark.asyncio
async def test_rate_limit_and_server_error() -> None:
    limited = _session((429, "slow down"))
    with pytest.raises(OdecetRateLimitError):
        await _client(limited).async_login()
    failed = _session((200, load_fixture("signin.html")), (503, "down"))
    with pytest.raises(OdecetTransportError):
        await _client(failed).async_login()


@pytest.mark.asyncio
async def test_timeout_is_transport() -> None:
    session = _session(TimeoutError("timed out"))
    with pytest.raises(OdecetTransportError):
        await _client(session).async_login()


@pytest.mark.asyncio
async def test_dashboard_that_is_a_login_page_is_auth() -> None:
    session = _session(
        (200, load_fixture("signin.html")),
        (200, "True"),
        (200, load_fixture("signin.html")),
    )
    with pytest.raises(OdecetAuthError):
        await _client(session).async_fetch(FetchMethod.TABLE, now=NOW)
