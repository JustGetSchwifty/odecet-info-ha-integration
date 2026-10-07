"""Diagnostics without the password, token, or cookies."""

from __future__ import annotations

from typing import Any

from homeassistant.core import HomeAssistant

from custom_components.odecet_info.const import (
    CONF_FETCH_METHOD,
    CONF_MEDIUMS,
    CONF_SYNC_FROM,
)
from custom_components.odecet_info.entry import OdecetConfigEntry
from custom_components.odecet_info.parse import measurement_kind
from custom_components.odecet_info.statistics import hourly_statistics


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant,
    entry: OdecetConfigEntry,
) -> dict[str, Any]:
    """Return meters, warnings, and the cooldown. Never the password."""
    del hass
    coordinator = entry.runtime_data
    data = coordinator.data
    meters: list[dict[str, object]] = []
    issues: list[dict[str, object]] = []
    if data is not None:
        issues = [
            {"code": issue.code, "message": issue.message, "serial": issue.serial}
            for issue in data.issues
        ]
        for meter in data.meters():
            statistic_points = (
                len(hourly_statistics(meter.readings))
                if measurement_kind(meter.unit) is not None
                else 0
            )
            meters.append(
                {
                    "medium": meter.medium.value,
                    "serial": meter.serial,
                    "unit": meter.unit,
                    "raw_unit": meter.raw_unit,
                    "points": len(meter.readings),
                    "oldest_at": meter.readings[0].timestamp.isoformat(),
                    "latest": str(meter.latest.value),
                    "latest_at": meter.latest.timestamp.isoformat(),
                    "statistic_points": statistic_points,
                }
            )
    return {
        "fetch_method": entry.options.get(CONF_FETCH_METHOD),
        "mediums": entry.options.get(CONF_MEDIUMS),
        "sync_from": entry.options.get(CONF_SYNC_FROM),
        "source": None if data is None else data.source,
        "failures": coordinator.failures,
        "cooldown_seconds": coordinator.cooldown_seconds,
        "next_manual_sync": coordinator.next_manual_sync.isoformat(),
        "issues": issues,
        "meters": meters,
    }
