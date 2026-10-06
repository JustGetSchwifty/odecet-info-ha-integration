"""Small HTML extractors for the sign-in form and the history table.

The pages are server-rendered. A full HTML library is avoided so the
integration does not add a dependency beyond what the client already needs.
"""

from __future__ import annotations

from dataclasses import dataclass
from html.parser import HTMLParser


@dataclass(frozen=True)
class FormField:
    """An input inside a form."""

    name: str
    value: str
    field_type: str


@dataclass(frozen=True)
class SelectField:
    """A select and the option values it can submit."""

    name: str
    options: tuple[str, ...]
    selected: str | None


@dataclass(frozen=True)
class HtmlForm:
    """Fields the client can resubmit."""

    action: str | None
    fields: tuple[FormField, ...]
    selects: tuple[SelectField, ...]


@dataclass(frozen=True)
class HtmlTable:
    """One table, header row included."""

    element_id: str | None
    rows: tuple[tuple[str, ...], ...]


class _PageParser(HTMLParser):
    """Collect forms and tables, including text nested inside cells."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.forms: list[HtmlForm] = []
        self.tables: list[HtmlTable] = []
        self._in_form = False
        self._form_action: str | None = None
        self._fields: list[FormField] = []
        self._selects: list[SelectField] = []
        self._in_select = False
        self._select_name: str | None = None
        self._select_options: list[str] = []
        self._select_selected: str | None = None
        self._in_option = False
        self._option_value: str | None = None
        self._option_selected = False
        self._option_text: list[str] = []
        self._in_table = False
        self._table_id: str | None = None
        self._rows: list[tuple[str, ...]] = []
        self._row: list[str] = []
        self._in_cell = False
        self._cell: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr = {name: value or "" for name, value in attrs}
        if tag == "form":
            self._in_form = True
            self._form_action = attr.get("action") or None
            self._fields = []
            self._selects = []
        elif tag == "input" and self._in_form and attr.get("name"):
            self._fields.append(
                FormField(attr["name"], attr.get("value", ""), attr.get("type", "text"))
            )
        elif tag == "select" and self._in_form and attr.get("name"):
            self._in_select = True
            self._select_name = attr["name"]
            self._select_options = []
            self._select_selected = None
        elif tag == "option" and self._in_select:
            self._in_option = True
            self._option_value = attr.get("value")
            self._option_selected = "selected" in attr
            self._option_text = []
        elif tag == "table":
            self._in_table = True
            self._table_id = attr.get("id") or None
            self._rows = []
        elif tag == "tr" and self._in_table:
            self._row = []
        elif tag in {"td", "th"} and self._in_table:
            self._in_cell = True
            self._cell = []

    def handle_endtag(self, tag: str) -> None:
        if tag == "option" and self._in_option:
            value = self._option_value
            if value is None:
                value = "".join(self._option_text).strip()
            self._select_options.append(value)
            if self._option_selected and self._select_selected is None:
                self._select_selected = value
            self._in_option = False
        elif tag == "select" and self._in_select and self._select_name:
            self._selects.append(
                SelectField(
                    self._select_name,
                    tuple(self._select_options),
                    self._select_selected,
                )
            )
            self._in_select = False
        elif tag == "form" and self._in_form:
            self.forms.append(
                HtmlForm(self._form_action, tuple(self._fields), tuple(self._selects))
            )
            self._in_form = False
        elif tag in {"td", "th"} and self._in_cell:
            text = " ".join("".join(self._cell).split())
            self._row.append(text)
            self._in_cell = False
        elif tag == "tr" and self._in_table and self._row:
            self._rows.append(tuple(self._row))
            self._row = []
        elif tag == "table" and self._in_table:
            self.tables.append(HtmlTable(self._table_id, tuple(self._rows)))
            self._in_table = False

    def handle_data(self, data: str) -> None:
        if self._in_cell:
            self._cell.append(data)
        if self._in_option:
            self._option_text.append(data)


def parse_page(html: str) -> tuple[tuple[HtmlForm, ...], tuple[HtmlTable, ...]]:
    """Return forms and tables in document order."""
    parser = _PageParser()
    parser.feed(html)
    parser.close()
    return tuple(parser.forms), tuple(parser.tables)


def is_sign_in_page(html: str) -> bool:
    """True when the body is the login form rather than the dashboard."""
    return 'id="kt_sign_in_form"' in html
