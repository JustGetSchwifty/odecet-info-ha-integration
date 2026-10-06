"""Synthetic readings shared by the Home Assistant tests."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

from custom_components.odecet_info.models import (
    Medium,
    Reading,
    ReadingIssue,
    ReadingSet,
)

PRAGUE = ZoneInfo("Europe/Prague")


def reading(
    medium: Medium,
    serial: str,
    value: str,
    unit: str | None,
    *,
    day: int = 5,
) -> Reading:
    return Reading(
        medium=medium,
        raw_type=medium.label,
        serial=serial,
        module_serial="2001",
        timestamp=datetime(2026, 10, day, 12, tzinfo=PRAGUE),
        value=Decimal(value),
        unit=unit,
        raw_unit="" if unit is None else unit,
    )


def sample_readings(*, heat: bool = True, cold: bool = True) -> ReadingSet:
    """Cold water grows from 10 to 12. Heat has a register and no unit."""
    rows: list[Reading] = []
    issues: list[ReadingIssue] = []
    if cold:
        rows.append(reading(Medium.COLD_WATER, "1001", "10", "m³", day=5))
        rows.append(reading(Medium.COLD_WATER, "1001", "12", "m³", day=6))
    if heat:
        rows.append(reading(Medium.HEAT, "1003", "140", None, day=5))
        issues.append(
            ReadingIssue(
                "missing_unit",
                "The site did not provide a unit",
                serial="1003",
            )
        )
    return ReadingSet(tuple(rows), tuple(issues), "csv")
