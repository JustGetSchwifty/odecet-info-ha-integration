"""Build hourly recorder points from a meter's register history.

`sum` is consumption, not the register. The first sample starts the sum at
zero. A decrease is a new meter cycle: the new register is added from zero
instead of subtracting. This matches Home Assistant `total_increasing`.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal

from custom_components.odecet_info.models import Reading


@dataclass(frozen=True)
class HourlyPoint:
    """One hour of statistics for a single meter."""

    start: datetime
    state: float
    sum: float
    last_reset: datetime | None = None


def hourly_statistics(readings: tuple[Reading, ...]) -> tuple[HourlyPoint, ...]:
    """Collapse samples into UTC hours. Empty input returns no points."""
    if not readings:
        return ()
    ordered = sorted(readings, key=lambda item: item.timestamp)
    buckets: dict[datetime, list[Reading]] = {}
    for reading in ordered:
        start = _hour_start(reading.timestamp)
        buckets.setdefault(start, []).append(reading)

    total = Decimal("0")
    previous: Decimal | None = None
    points: list[HourlyPoint] = []
    for start in sorted(buckets):
        samples = buckets[start]
        reset_at: datetime | None = None
        for sample in samples:
            if previous is None:
                previous = sample.value
                continue
            if sample.value >= previous:
                total += sample.value - previous
            else:
                total += sample.value
                reset_at = sample.timestamp.astimezone(UTC)
            previous = sample.value
        points.append(
            HourlyPoint(
                start=start,
                state=float(samples[-1].value),
                sum=float(total),
                last_reset=reset_at,
            )
        )
    return tuple(points)


def _hour_start(moment: datetime) -> datetime:
    utc = moment.astimezone(UTC)
    return utc.replace(minute=0, second=0, microsecond=0)
