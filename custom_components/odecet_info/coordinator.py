"""Daily fetch with a shared one-minute gate for manual and automatic sync."""

from __future__ import annotations

import logging
import random
from datetime import date, datetime, timedelta

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.event import async_track_point_in_time
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from custom_components.odecet_info.client import OdecetClient
from custom_components.odecet_info.const import (
    BACKOFF_CAP,
    CONF_FETCH_METHOD,
    CONF_MEDIUMS,
    CONF_PASSWORD,
    CONF_SIGNIN_URL,
    CONF_SYNC_FROM,
    CONF_USERNAME,
    DAILY_HOUR,
    DAILY_JITTER,
    DOMAIN,
    MAX_FAILURES,
    MIN_SYNC_INTERVAL,
)
from custom_components.odecet_info.errors import OdecetAuthError, OdecetError
from custom_components.odecet_info.models import FetchMethod, ReadingSet

_LOGGER = logging.getLogger(__name__)


class OdecetCoordinator(DataUpdateCoordinator[ReadingSet]):
    """One account, one in-flight fetch, at most one attempt per minute."""

    def __init__(self, hass: HomeAssistant, entry) -> None:
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=None,
        )
        self._unsub_schedule = None
        self._last_attempt: datetime | None = None
        self.failures = 0

    @property
    def manual_sync_allowed(self) -> bool:
        """True when the shared cooldown has elapsed."""
        if self._last_attempt is None:
            return True
        return dt_util.utcnow() - self._last_attempt >= MIN_SYNC_INTERVAL

    @property
    def next_manual_sync(self) -> datetime:
        """UTC time when the next attempt is allowed."""
        if self._last_attempt is None:
            return dt_util.utcnow()
        return self._last_attempt + MIN_SYNC_INTERVAL

    @property
    def cooldown_seconds(self) -> int:
        """Whole seconds until a manual sync is allowed."""
        remaining = (self.next_manual_sync - dt_util.utcnow()).total_seconds()
        return max(0, int(remaining))

    async def async_shutdown(self) -> None:
        """Cancel the daily schedule and the coordinator listener."""
        if self._unsub_schedule is not None:
            self._unsub_schedule()
            self._unsub_schedule = None
        await super().async_shutdown()

    async def _async_update_data(self) -> ReadingSet:
        self._last_attempt = dt_util.utcnow()
        try:
            result = await self._fetch()
        except OdecetAuthError as err:
            self.failures += 1
            _LOGGER.warning("odecet.info rejected the saved account")
            raise ConfigEntryAuthFailed(str(err)) from err
        except OdecetError as err:
            self.failures += 1
            _LOGGER.warning("odecet.info sync failed: %s", err)
            self._schedule_after_failure()
            raise UpdateFailed(str(err)) from err
        self.failures = 0
        ir.async_delete_issue(self.hass, DOMAIN, "sync_failed")
        self._schedule_daily()
        self._sync_unit_issues(result)
        return result

    async def _fetch(self) -> ReadingSet:
        entry = self.config_entry
        if entry is None:
            raise UpdateFailed("The config entry was removed")
        raw_start = entry.options.get(CONF_SYNC_FROM) or None
        sync_from = date.fromisoformat(raw_start) if raw_start else None
        method = FetchMethod(entry.options.get(CONF_FETCH_METHOD, FetchMethod.AUTO.value))
        client = OdecetClient(
            async_get_clientsession(self.hass),
            entry.data[CONF_SIGNIN_URL],
            entry.data[CONF_USERNAME],
            entry.data[CONF_PASSWORD],
        )
        return await client.async_fetch(method, sync_from)

    def _schedule_daily(self) -> None:
        local_now = dt_util.now()
        target = local_now.replace(hour=DAILY_HOUR, minute=0, second=0, microsecond=0)
        if target <= local_now:
            target += timedelta(days=1)
        jitter = timedelta(seconds=random.uniform(0, DAILY_JITTER.total_seconds()))
        self._schedule(dt_util.as_utc(target + jitter))

    def _schedule_after_failure(self) -> None:
        if self.failures >= MAX_FAILURES:
            ir.async_create_issue(
                self.hass,
                DOMAIN,
                "sync_failed",
                is_fixable=False,
                severity=ir.IssueSeverity.ERROR,
                translation_key="sync_failed",
                translation_placeholders={"attempts": str(self.failures)},
            )
            self._schedule_daily()
            return
        base = min(MIN_SYNC_INTERVAL * (2 ** (self.failures - 1)), BACKOFF_CAP)
        spread = random.uniform(0, base.total_seconds() * 0.2)
        delay = max(MIN_SYNC_INTERVAL, base + timedelta(seconds=spread))
        self._schedule(dt_util.utcnow() + delay)

    def _schedule(self, when: datetime) -> None:
        if self._unsub_schedule is not None:
            self._unsub_schedule()
        self._unsub_schedule = async_track_point_in_time(self.hass, self._handle_scheduled, when)

    async def _handle_scheduled(self, _now: datetime) -> None:
        if not self.manual_sync_allowed:
            self._schedule(self.next_manual_sync)
            return
        await self.async_request_refresh()

    def _sync_unit_issues(self, result: ReadingSet) -> None:
        entry = self.config_entry
        enabled = set(entry.options.get(CONF_MEDIUMS, [])) if entry else set()
        active: set[str] = set()
        for meter in result.meters():
            if meter.medium.value not in enabled:
                continue
            issue_id = f"missing_unit_{meter.serial}"
            if meter.unit is None:
                active.add(issue_id)
                ir.async_create_issue(
                    self.hass,
                    DOMAIN,
                    issue_id,
                    is_fixable=False,
                    severity=ir.IssueSeverity.WARNING,
                    translation_key="missing_unit",
                    translation_placeholders={"serial": meter.serial},
                )
            else:
                ir.async_delete_issue(self.hass, DOMAIN, issue_id)
        registry = ir.async_get(self.hass)
        for issue_id in list(registry.issues):
            domain, parsed_id = issue_id
            if domain != DOMAIN or not parsed_id.startswith("missing_unit_"):
                continue
            if parsed_id not in active:
                ir.async_delete_issue(self.hass, DOMAIN, parsed_id)
