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

The user chooses `auto`, `csv`, or `table`.

- `auto` tries the CSV export, then the history table.
- A CSV response that is actually the login HTML is a failure of that method, not an empty dataset.
- Parse Czech dates as `DD.MM.YYYY` in `Europe/Prague`.
- Accept a decimal comma. Store values as `Decimal`.
- Map meter types only through the alias table in the parser. Unknown types stay unknown and are reported.
- Attach a unit only when the header or the cell contains one. Do not guess `m³` or `kWh`.

## Fixtures

Discovery output goes to gitignored `dev/capture/`. When the live shape changes, update `docs/website-contract.md` and add a synthetic fixture that copies the shape without real serials, emails, or addresses.

Extend `parse_csv` and `parse_history_html`. Do not create a third parser for a small column rename; add a header alias.
