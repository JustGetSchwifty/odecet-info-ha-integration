"""Internal reading model. Values stay decimal until a Home Assistant boundary."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import StrEnum


class Medium(StrEnum):
    """Meter types the integration knows how to offer."""

    COLD_WATER = "cold_water"
    HOT_WATER = "hot_water"
    HEAT = "heat"

    @property
    def label(self) -> str:
        """English name used in forms and device names."""
        labels = {
            Medium.COLD_WATER: "Cold water",
            Medium.HOT_WATER: "Hot water",
            Medium.HEAT: "Heat",
        }
        return labels[self]


class FetchMethod(StrEnum):
    """How a sync reads the dashboard."""

    AUTO = "auto"
    CSV = "csv"
    TABLE = "table"


@dataclass(frozen=True)
class Reading:
    """One register sample from the history table."""

    medium: Medium
    raw_type: str
    serial: str
    module_serial: str | None
    timestamp: datetime
    value: Decimal
    unit: str | None
    raw_unit: str


@dataclass(frozen=True)
class ReadingIssue:
    """A row or document problem that did not abort the whole sync."""

    code: str
    message: str
    row: int | None = None
    serial: str | None = None


@dataclass(frozen=True)
class Meter:
    """Readings that belong to one physical meter, oldest first."""

    medium: Medium
    serial: str
    module_serial: str | None
    unit: str | None
    raw_unit: str
    readings: tuple[Reading, ...]

    @property
    def latest(self) -> Reading:
        """Newest register sample."""
        return self.readings[-1]


@dataclass(frozen=True)
class ReadingSet:
    """Everything one fetch produced."""

    readings: tuple[Reading, ...]
    issues: tuple[ReadingIssue, ...]
    source: str

    def meters(self) -> tuple[Meter, ...]:
        """Group readings by medium and serial."""
        grouped: dict[tuple[Medium, str], list[Reading]] = {}
        for reading in self.readings:
            grouped.setdefault((reading.medium, reading.serial), []).append(reading)
        meters: list[Meter] = []
        for (medium, serial), items in grouped.items():
            ordered = tuple(sorted(items, key=lambda item: item.timestamp))
            latest = ordered[-1]
            meters.append(
                Meter(
                    medium=medium,
                    serial=serial,
                    module_serial=latest.module_serial,
                    unit=latest.unit,
                    raw_unit=latest.raw_unit,
                    readings=ordered,
                )
            )
        return tuple(sorted(meters, key=lambda meter: (meter.medium.value, meter.serial)))

    def mediums(self) -> tuple[Medium, ...]:
        """Meter types present in this set, in enum order."""
        present = {meter.medium for meter in self.meters()}
        return tuple(medium for medium in Medium if medium in present)
