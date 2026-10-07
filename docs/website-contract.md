# odecet.info website contract

<p align="center">
  <a href="website-contract.md"><img alt="English" src="https://img.shields.io/badge/English-1f6feb?style=for-the-badge"></a>
  <a href="cs/website-contract.md"><img alt="Čeština" src="https://img.shields.io/badge/%C4%8Ce%C5%A1tina-6e7681?style=for-the-badge"></a>
</p>

Observed on 6 October 2026 against the live site. The capture used to confirm this lives in gitignored `dev/capture/`. Fixtures in `tests/fixtures/` copy the shape with invented values.

## Sign-in

`GET https://odecet.info/signin` returns an HTML form.

| Item | Value |
| --- | --- |
| Form id | `kt_sign_in_form` |
| Form action | `signin` (same URL) |
| Success check | POST body is exactly `True` |
| Antiforgery field | `__RequestVerificationToken`, copied from the form |
| Account field | `email` |
| Secret field | `password` |
| Honeypot | `website`, must be posted empty |
| Cookies | Keep the jar for this sign-in only, including `ARRAffinity` |

`ARRAffinity` sticks the browser to one server. It is not a login that lasts for months. The form has no remember-me field, so a Netscape `cookies.txt` export would expire with the browser session. Do not add a cookie sign-in unless a later capture shows an authentication cookie with a long `Expires` or `Max-Age`.

Any other 200 body is invalid credentials. HTTP 429 is rate limiting. Timeouts and HTTP 5xx are transport failures. A missing token means the page structure changed.

The browser posts `multipart/form-data` through axios. The client does the same.

## Dashboard

After sign-in, `GET /` is the dashboard. It is server-rendered HTML, not a JSON API.

A `GET` form on `/` selects the period:

| Field | Meaning |
| --- | --- |
| `flat` | Hidden account key. Read it from the page. Do not hard-code it. |
| `fromMonth`, `fromYear` | Period start. Months are `1`–`12`. |
| `toMonth`, `toYear` | Period end. |

The default period is about twelve months. The integration re-requests the form from the sync-from month, or from the earliest year in the form when sync-from is empty, through the current month. Readings are then filtered to the exact start date, because the form is monthly.

## History table

The register history is the table `kt_ecommerce_report_customer_orders_table`. DataTables paginates it in the browser. The rows are already in the HTML, so the client does not walk pages.

If that id disappears, the parser uses the table whose header contains the type and register columns.

| Column | Internal field | Notes |
| --- | --- | --- |
| Typ měřiče | medium | Often wrapped in a `div` badge. Read the text. |
| Výrobní číslo | serial | Identity of the physical meter. |
| Výrobní číslo modulu | module serial | Attribute. It does not split a meter. |
| Datum | timestamp | `DD.MM.YYYY`, `Europe/Prague`, stored at 12:00 local. |
| Stav | value | Register. Dot or comma decimals. `Decimal`. |
| Jednotka | unit | See below. |

Known type labels:

| Label | Medium |
| --- | --- |
| Studená voda | `cold_water` |
| Teplá voda | `hot_water` |
| Teplo | `heat` |

Matching is case-insensitive and also accepts the same words without diacritics, plus `cold water`, `hot water`, and `heat`.

## Units

| Site text | Stored unit | Home Assistant device class |
| --- | --- | --- |
| `m3`, `m³`, `m^3` | `m³` | `water` for cold and hot water |
| `L`, `l` | `L` | `water` |
| `kWh`, `GJ`, `MJ`, `Wh`, `MWh` | canonical energy unit | `energy` for heat |

On the observed account, water rows use `m3` and every heat row has an empty `Jednotka` cell. That empty heat cell is stored as `scale units`. It is not converted to `kWh` or `GJ`. A water row with an empty unit stays missing and raises a repair. A heat row that actually contains an energy unit keeps that unit.

## CSV export

The **Exportovat do CSV** button is a DataTables `csvHtml5` button in `meter-tables.js`. It does not request a file from the server. It serializes the history table.

Fetch methods:

| Method | Behavior |
| --- | --- |
| `table` | Parse the HTML cells. |
| `csv` | If a real CSV link exists, download it. Otherwise serialize the history table to CSV and parse that text. |
| `auto` | CSV path first, then the HTML table. |

A response that is the sign-in page is a failed fetch, not an empty history.

## Rows the parser drops or keeps

| Situation | Result |
| --- | --- |
| Exact duplicate of serial, module, timestamp, and value | One row, plus a warning |
| Same serial and timestamp, different value | Keep the later row, plus a warning |
| Unparseable date or value | Skip the row |
| Date more than two days in the future | Skip the row |
| Unknown meter type | Skip the row |
| Missing unit | Keep the row |
| Register lower than the previous reading | Keep the row and warn |

The monthly summary table (`kt_seznam_meraku_table`) and the chart JSON are consumption totals for the dashboard. They are not the register history and the integration does not parse them.
