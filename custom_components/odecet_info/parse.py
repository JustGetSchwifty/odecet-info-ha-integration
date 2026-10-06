"""Turn the history table or its CSV export into readings.

Parsers do not open sockets. A single bad row becomes a warning. A document
that does not have the known columns is a structure error.
"""

from __future__ import annotations

import csv
import io
import re
import unicodedata
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation
from zoneinfo import ZoneInfo

from custom_components.odecet_info.errors import OdecetStructureError
from custom_components.odecet_info.html_extract import HtmlTable, parse_page
from custom_components.odecet_info.models import (
    Medium,
    Reading,
    ReadingIssue,
    ReadingSet,
)

HISTORY_TABLE_ID = "kt_ecommerce_report_customer_orders_table"
SITE_TIMEZONE = ZoneInfo("Europe/Prague")
# A reading dated slightly ahead of the clock is accepted. Further ahead is not.
FUTURE_SKEW = timedelta(days=2)

HEADER_ALIASES = {
    "typ merice": "type",
    "meter type": "type",
    "type": "type",
    "vyrobni cislo": "serial",
    "serial": "serial",
    "vyrobni cislo modulu": "module",
    "module serial": "module",
    "datum": "date",
    "date": "date",
    "stav": "value",
    "state": "value",
    "register": "value",
    "jednotka": "unit",
    "unit": "unit",
}

TYPE_ALIASES = {
    "studena voda": Medium.COLD_WATER,
    "cold water": Medium.COLD_WATER,
    "tepla voda": Medium.HOT_WATER,
    "hot water": Medium.HOT_WATER,
    "teplo": Medium.HEAT,
    "topeni": Medium.HEAT,
    "heat": Medium.HEAT,
}

# Spelling variants of a unit the site actually printed. Not a guess of a missing unit.
UNIT_ALIASES = {
    "m3": "m³",
    "m³": "m³",
    "m^3": "m³",
    "l": "L",
    "ltr": "L",
    "kwh": "kWh",
    "wh": "Wh",
    "mwh": "MWh",
    "gj": "GJ",
    "mj": "MJ",
}

VOLUME_UNITS = frozenset({"m³", "L"})
ENERGY_UNITS = frozenset({"kWh", "Wh", "MWh", "GJ", "MJ"})
REQUIRED_COLUMNS = frozenset({"type", "serial", "date", "value"})


def measurement_kind(unit: str | None) -> str | None:
    """Return `volume` or `energy` when the unit is one Home Assistant understands."""
    if unit in VOLUME_UNITS:
        return "volume"
    if unit in ENERGY_UNITS:
        return "energy"
    return None


def parse_history_html(html: str, *, now: datetime | None = None) -> ReadingSet:
    """Parse the dashboard history table."""
    _forms, tables = parse_page(html)
    table = choose_history_table(tables)
    if table is None:
        raise OdecetStructureError("History table was not found")
    if not table.rows:
        return ReadingSet((), (), "table")
    return _parse_matrix(table.rows, source="table", now=now)


def history_as_csv(html: str) -> str:
    """Serialize the history table the way the in-browser CSV button does."""
    _forms, tables = parse_page(html)
    table = choose_history_table(tables)
    if table is None:
        raise OdecetStructureError("History table was not found")
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    for row in table.rows:
        writer.writerow(row)
    return buffer.getvalue()


def parse_csv(text: str, *, now: datetime | None = None) -> ReadingSet:
    """Parse a CSV export. A login page or a headerless file is a structure error."""
    stripped = text.lstrip("\ufeff").strip()
    if not stripped:
        raise OdecetStructureError("CSV export was empty")
    if 'id="kt_sign_in_form"' in stripped or stripped.startswith("<!DOCTYPE"):
        raise OdecetStructureError("CSV export returned a web page")
    sample = stripped.splitlines()[0]
    delimiter = ";" if sample.count(";") > sample.count(",") else ","
    reader = csv.reader(io.StringIO(stripped), delimiter=delimiter)
    rows = [
        tuple(cell.strip() for cell in row)
        for row in reader
        if any(cell.strip() for cell in row)
    ]
    if len(rows) < 1:
        raise OdecetStructureError("CSV export has no header")
    return _parse_matrix(tuple(rows), source="csv", now=now)


def choose_history_table(tables: tuple[HtmlTable, ...]) -> HtmlTable | None:
    """Prefer the known id, then any table that has the register columns."""
    for table in tables:
        if table.element_id == HISTORY_TABLE_ID:
            return table
    for table in tables:
        if table.rows and REQUIRED_COLUMNS <= set(map_headers(table.rows[0]).values()):
            return table
    return None


def map_headers(header: tuple[str, ...]) -> dict[int, str]:
    """Map a column index to a field name."""
    mapping: dict[int, str] = {}
    for index, cell in enumerate(header):
        name, _unit = split_header(cell)
        field = HEADER_ALIASES.get(_fold(name))
        if field and field not in mapping.values():
            mapping[index] = field
    return mapping


def split_header(cell: str) -> tuple[str, str | None]:
    """Split `Stav [m3]` into the name and an optional unit hint."""
    match = re.match(r"^(.*?)(?:\s*[\[(]\s*([^)\]]+?)\s*[\])])?\s*$", cell.strip())
    if match is None:
        return cell.strip(), None
    unit = match.group(2)
    return match.group(1).strip(), unit.strip() if unit else None


def header_unit(header: tuple[str, ...]) -> str | None:
    """Unit written on the value column, if the site put it in the header."""
    for cell in header:
        name, unit = split_header(cell)
        if HEADER_ALIASES.get(_fold(name)) == "value" and unit:
            return normalize_unit(unit)[0]
    return None


def normalize_unit(raw: str) -> tuple[str | None, str | None]:
    """Return `(canonical unit, issue code)`.

    An empty cell is missing. A non-empty unknown token is not mapped.
    """
    text = raw.strip()
    if not text:
        return None, "missing_unit"
    canonical = UNIT_ALIASES.get(text.casefold())
    if canonical is None:
        return None, "unknown_unit"
    return canonical, None


def _parse_matrix(
    rows: tuple[tuple[str, ...], ...],
    *,
    source: str,
    now: datetime | None,
) -> ReadingSet:
    header = rows[0]
    columns = map_headers(header)
    if not REQUIRED_COLUMNS <= set(columns.values()):
        raise OdecetStructureError("History columns were not recognized")
    default_unit = header_unit(header)
    index_of = {field: index for index, field in columns.items()}
    parsed: list[Reading] = []
    issues: list[ReadingIssue] = []
    for offset, row in enumerate(rows[1:], start=2):
        reading, issue = _parse_row(row, index_of, default_unit, offset, now)
        if issue is not None:
            issues.append(issue)
        if reading is not None:
            parsed.append(reading)
    readings, extra = _collapse(parsed)
    issues.extend(extra)
    issues.extend(_decrease_issues(readings))
    return ReadingSet(tuple(readings), tuple(issues), source)


def _parse_row(
    row: tuple[str, ...],
    index_of: dict[str, int],
    default_unit: str | None,
    row_number: int,
    now: datetime | None,
) -> tuple[Reading | None, ReadingIssue | None]:
    def cell(field: str) -> str:
        index = index_of.get(field)
        if index is None or index >= len(row):
            return ""
        return row[index].strip()

    raw_type = cell("type")
    serial = cell("serial")
    if not raw_type and not serial:
        return None, None
    medium = TYPE_ALIASES.get(_fold(raw_type))
    if medium is None:
        return None, ReadingIssue(
            "unknown_type",
            f"Unknown meter type {raw_type!r}",
            row_number,
            serial or None,
        )
    if not serial:
        return None, ReadingIssue("missing_serial", "Meter serial is empty", row_number)
    try:
        timestamp = _parse_timestamp(cell("date"), now)
    except ValueError as err:
        code = "future_date" if str(err) == "future" else "bad_date"
        return None, ReadingIssue(
            code,
            f"Date {cell('date')!r} was rejected",
            row_number,
            serial,
        )
    try:
        value = _parse_decimal(cell("value"))
    except InvalidOperation:
        return None, ReadingIssue(
            "bad_value",
            f"Register value {cell('value')!r} is not a number",
            row_number,
            serial,
        )
    raw_unit = cell("unit")
    unit, unit_issue = normalize_unit(raw_unit)
    if unit is None and not raw_unit and default_unit:
        unit = default_unit
        unit_issue = None
    reading = Reading(
        medium=medium,
        raw_type=raw_type,
        serial=serial,
        module_serial=cell("module") or None,
        timestamp=timestamp,
        value=value,
        unit=unit,
        raw_unit=raw_unit,
    )
    issue = None
    if unit_issue == "unknown_unit":
        issue = ReadingIssue(
            "unknown_unit",
            f"Unit {raw_unit!r} is not recognized",
            row_number,
            serial,
        )
    elif unit_issue == "missing_unit":
        issue = ReadingIssue(
            "missing_unit",
            "The site did not provide a unit",
            row_number,
            serial,
        )
    return reading, issue


def _collapse(readings: list[Reading]) -> tuple[list[Reading], list[ReadingIssue]]:
    """Drop exact copies. Keep the later row when the same timestamp disagrees."""
    issues: list[ReadingIssue] = []
    exact: set[tuple[object, ...]] = set()
    by_moment: dict[tuple[Medium, str, datetime], Reading] = {}
    order: list[tuple[Medium, str, datetime]] = []
    for reading in readings:
        identity = (
            reading.medium,
            reading.serial,
            reading.module_serial,
            reading.timestamp,
            reading.value,
        )
        if identity in exact:
            issues.append(
                ReadingIssue(
                    "duplicate",
                    "Duplicate reading was ignored",
                    serial=reading.serial,
                )
            )
            continue
        exact.add(identity)
        moment = (reading.medium, reading.serial, reading.timestamp)
        previous = by_moment.get(moment)
        if previous is None:
            order.append(moment)
        elif previous.value != reading.value:
            issues.append(
                ReadingIssue(
                    "conflicting_value",
                    "Two register values share a timestamp; the later row was kept",
                    serial=reading.serial,
                )
            )
        by_moment[moment] = reading
    return [by_moment[moment] for moment in order], issues


def _decrease_issues(readings: list[Reading]) -> list[ReadingIssue]:
    issues: list[ReadingIssue] = []
    previous: dict[tuple[Medium, str], Decimal] = {}
    ordered = sorted(readings, key=lambda item: item.timestamp)
    for reading in ordered:
        key = (reading.medium, reading.serial)
        prior = previous.get(key)
        if prior is not None and reading.value < prior:
            issues.append(
                ReadingIssue(
                    "decrease",
                    "Register decreased and was kept as a possible meter reset",
                    serial=reading.serial,
                )
            )
        previous[key] = reading.value
    return issues


def _parse_timestamp(raw: str, now: datetime | None) -> datetime:
    text = raw.strip()
    parsed: datetime | None = None
    for fmt in ("%d.%m.%Y", "%Y-%m-%d"):
        try:
            parsed = datetime.strptime(text, fmt)
            break
        except ValueError:
            continue
    if parsed is None:
        raise ValueError("bad")
    local = parsed.replace(hour=12, tzinfo=SITE_TIMEZONE)
    current = now.astimezone(SITE_TIMEZONE) if now else datetime.now(SITE_TIMEZONE)
    if local > current + FUTURE_SKEW:
        raise ValueError("future")
    return local


def _parse_decimal(raw: str) -> Decimal:
    text = raw.strip().replace("\xa0", "").replace(" ", "")
    if not text:
        raise InvalidOperation
    if "," in text and "." in text:
        if text.rfind(",") > text.rfind("."):
            text = text.replace(".", "").replace(",", ".")
        else:
            text = text.replace(",", "")
    elif "," in text:
        text = text.replace(",", ".")
    try:
        return Decimal(text)
    except InvalidOperation:
        raise


def _fold(text: str) -> str:
    stripped = unicodedata.normalize("NFKD", text)
    ascii_text = stripped.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"\s+", " ", ascii_text).casefold().strip()
