"""Optimistic and pessimistic parser coverage. No network."""

from datetime import datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

import pytest
from custom_components.odecet_info.errors import OdecetStructureError
from custom_components.odecet_info.models import Medium
from custom_components.odecet_info.parse import (
    history_as_csv,
    normalize_unit,
    parse_csv,
    parse_history_html,
)
from tests.fakes import load_fixture

PRAGUE = ZoneInfo("Europe/Prague")
NOW = datetime(2026, 10, 6, 12, tzinfo=PRAGUE)


def test_html_and_csv_agree_on_the_happy_path() -> None:
    """The same meters come out of the table and of a CSV with the same rows."""
    html = parse_history_html(load_fixture("dashboard.html"), now=NOW)
    csv_text = load_fixture("history.csv")
    csv_parsed = parse_csv(csv_text, now=NOW)

    cold = html.meters()[0]
    assert cold.medium is Medium.COLD_WATER
    assert cold.serial == "1001"
    assert cold.unit == "m³"
    assert cold.latest.value == Decimal("35.477")
    assert cold.latest.timestamp == datetime(2026, 10, 5, 12, tzinfo=PRAGUE)

    hot = next(meter for meter in html.meters() if meter.medium is Medium.HOT_WATER)
    assert hot.latest.value == Decimal("21.104")
    assert hot.unit == "m³"

    heat = next(meter for meter in html.meters() if meter.medium is Medium.HEAT)
    assert heat.latest.value == Decimal("140")
    assert heat.unit is None

    csv_serials = {meter.serial for meter in csv_parsed.meters()}
    assert csv_serials == {"1001", "1002", "1003"}
    cold_units = {meter.unit for meter in csv_parsed.meters() if meter.serial == "1001"}
    assert cold_units == {"m³"}


def test_serialized_table_parses_as_csv() -> None:
    html = load_fixture("dashboard.html")
    rendered = history_as_csv(html)
    from_csv = parse_csv(rendered, now=NOW)
    from_html = parse_history_html(html, now=NOW)
    assert [meter.latest.value for meter in from_csv.meters()] == [
        meter.latest.value for meter in from_html.meters()
    ]


def test_duplicate_rows_collapse_and_problems_are_kept() -> None:
    parsed = parse_history_html(load_fixture("dashboard.html"), now=NOW)
    codes = {issue.code for issue in parsed.issues}
    assert "duplicate" in codes
    assert "unknown_type" in codes
    assert "bad_date" in codes
    assert "bad_value" in codes
    assert "future_date" in codes
    assert "missing_unit" in codes
    assert "unknown_unit" in codes
    assert "decrease" in codes
    cold_points = next(meter for meter in parsed.meters() if meter.serial == "1001")
    # The 2020 sample is still present here. The client applies the sync window.
    assert Decimal("1.000") in {reading.value for reading in cold_points.readings}
    assert all(reading.serial != "1004" for reading in parsed.readings)
    unknown_unit = [
        reading for reading in parsed.readings if reading.serial == "1006" and reading.unit is None
    ]
    assert unknown_unit


def test_semicolon_csv_and_decimal_thousands() -> None:
    text = "Typ měřiče;Výrobní číslo;Datum;Stav;Jednotka\nStudená voda;1001;05.10.2026;1.234,5;m3\n"
    parsed = parse_csv(text, now=NOW)
    assert parsed.readings[0].value == Decimal("1234.5")
    assert parsed.readings[0].unit == "m³"


def test_header_unit_is_used_when_the_cell_is_empty() -> None:
    text = "Typ měřiče,Výrobní číslo,Datum,Stav [kWh]\nTeplo,1003,05.10.2026,12\n"
    parsed = parse_csv(text, now=NOW)
    assert parsed.readings[0].unit == "kWh"
    assert not any(issue.code == "missing_unit" for issue in parsed.issues)


def test_conflicting_timestamp_keeps_the_later_row() -> None:
    text = (
        "Typ měřiče,Výrobní číslo,Datum,Stav,Jednotka\n"
        "Studená voda,1001,05.10.2026,10,m3\n"
        "Studená voda,1001,05.10.2026,11,m3\n"
    )
    parsed = parse_csv(text, now=NOW)
    assert parsed.readings[0].value == Decimal("11")
    assert any(issue.code == "conflicting_value" for issue in parsed.issues)


def test_login_page_is_not_an_empty_export() -> None:
    with pytest.raises(OdecetStructureError):
        parse_csv(load_fixture("signin.html"), now=NOW)


def test_missing_columns_are_a_structure_error() -> None:
    with pytest.raises(OdecetStructureError):
        parse_csv("Hello,World\n1,2\n", now=NOW)


def test_empty_history_table_is_an_empty_set() -> None:
    html = """
    <table id="kt_ecommerce_report_customer_orders_table">
      <tr><th>Typ měřiče</th><th>Výrobní číslo</th><th>Datum</th><th>Stav</th></tr>
    </table>
    """
    parsed = parse_history_html(html, now=NOW)
    assert parsed.readings == ()


def test_unknown_unit_spellings() -> None:
    assert normalize_unit("") == (None, "missing_unit")
    assert normalize_unit("m3") == ("m³", None)
    assert normalize_unit("GJ") == ("GJ", None)
    assert normalize_unit("buckets") == (None, "unknown_unit")
