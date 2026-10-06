"""Hourly statistics from register samples."""

from datetime import datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

from custom_components.odecet_info.models import Medium, Reading
from custom_components.odecet_info.statistics import hourly_statistics

PRAGUE = ZoneInfo("Europe/Prague")


def _reading(day: int, hour: int, value: str, serial: str = "1001") -> Reading:
    return Reading(
        medium=Medium.COLD_WATER,
        raw_type="Studená voda",
        serial=serial,
        module_serial="2001",
        timestamp=datetime(2026, 10, day, hour, tzinfo=PRAGUE),
        value=Decimal(value),
        unit="m³",
        raw_unit="m3",
    )


def test_sum_grows_by_positive_deltas() -> None:
    points = hourly_statistics((_reading(5, 8, "10"), _reading(5, 9, "12"), _reading(6, 8, "15")))
    assert [point.sum for point in points] == [0.0, 2.0, 5.0]
    assert [point.state for point in points] == [10.0, 12.0, 15.0]
    assert all(point.start.minute == 0 for point in points)
    assert all(point.start.tzinfo is not None for point in points)


def test_samples_in_one_hour_keep_the_last_state() -> None:
    points = hourly_statistics((_reading(5, 8, "10"), _reading(5, 8, "14")))
    assert len(points) == 1
    assert points[0].state == 14.0
    assert points[0].sum == 4.0


def test_decrease_starts_a_new_cycle() -> None:
    points = hourly_statistics((_reading(5, 8, "15"), _reading(6, 8, "3")))
    assert points[-1].state == 3.0
    assert points[-1].sum == 3.0
    assert points[-1].last_reset is not None


def test_empty_history_has_no_points() -> None:
    assert hourly_statistics(()) == ()
