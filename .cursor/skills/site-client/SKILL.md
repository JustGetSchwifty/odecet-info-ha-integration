---
name: site-client
description: Work on the odecet.info login client and measurement parsers. Use when changing sign-in, CSV export, the history table, units, or synthetic fixtures.
---

# Site client

odecet.info is an ASP.NET site. The sign-in page is HTML, not a JSON API.

## Login

1. `GET` the sign-in URL and keep the cookie jar (`ARRAffinity` plus the antiforgery cookie).
2. Read `__RequestVerificationToken` from the form. A missing token is a structure error, not a bad password.
3. `POST` `multipart/form-data` with `email`, `password`, `__RequestVerificationToken`, and an empty `website` field. The empty `website` field is a honeypot. Do not put a value in it.
4. A body of exactly `True` means success. Any other body is invalid credentials. A timeout, connection error, or HTTP 5xx is transport. HTTP 429 is rate limit.
5. Reject an obviously invalid email or an empty password locally before the POST.

## Fetching readings

The history is the server-rendered table `kt_ecommerce_report_customer_orders_table` on `GET /`. DataTables only paginates it in the browser. Re-request the period with the hidden `flat` field and `fromMonth` / `fromYear` / `toMonth` / `toYear`. Read `flat` from the page.

The CSV button is DataTables `csvHtml5`. There is no CSV URL today.

- `csv` downloads a real CSV link when one exists, otherwise serializes that table and parses the CSV.
- `table` reads the HTML cells.
- `auto` tries the CSV path, then the HTML table.
- A sign-in page returned instead of the dashboard fails that method.
- Parse `DD.MM.YYYY` as `Europe/Prague` at 12:00 local. Accept a decimal comma or dot. Store `Decimal`.
- Map meter types only through the alias table. Unknown types are skipped and reported.
- Normalize `m3` to `m³`. An empty unit stays empty. Do not invent `kWh` or `GJ` for heat.

## Fixtures

Discovery output goes to gitignored `dev/capture/`. When the live shape changes, update `docs/website-contract.md` and add a synthetic fixture that copies the shape without real serials, emails, or addresses.

Extend `parse_csv` and `parse_history_html`. Do not create a third parser for a small column rename; add a header alias.
