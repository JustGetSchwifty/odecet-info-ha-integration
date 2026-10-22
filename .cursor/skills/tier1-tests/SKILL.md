---
name: tier1-tests
description: Run and extend the fast pytest suite for the odecet.info client, parsers, and Home Assistant integration. Use before calling any larger chunk done, and when adding optimistic or pessimistic tests.
---

# Tier 1 tests

Tier 1 is the local pytest suite. It does not start Docker and it does not contact odecet.info.

## When to run

Run the suite after a larger chunk of parser, client, or integration work, and before describing that chunk as done.

```bash
uv run pytest
```

Parser-only changes can use `uv run pytest tests/test_parse.py tests/test_client.py`. Integration changes run the full suite.

## What a new test must cover

Add both sides when behavior changes:

- Optimistic: valid login body `True`, a CSV and an HTML table that become the same readings, a config flow that creates an entry.
- Pessimistic: bad credentials, missing antiforgery token, honeypot rejection if the server exposes it, timeout, HTTP 429 and 5xx, a login page returned instead of CSV, missing columns, decimal comma, `DD.MM.YYYY`, duplicate rows, missing unit, a decreasing register, dates outside the sync window, cooldown rejection, and a disabled medium left out.
- Guard: `tests/test_publish.py` scans the integration source and fails if it reads another integration's storage, including a `Store` opened under that integration's file name. A profile language saved by the frontend must not change setup text or meter device names. Those follow `hass.config.language`.

## Rules

- Mock HTTP with `aiohttp` test utilities or a fake session. Never use the live `.env` account in pytest.
- Fixtures live in `tests/fixtures/` and contain invented serials and values.
- Home Assistant tests request the `hass` and `enable_custom_integrations` fixtures from `pytest-homeassistant-custom-component`.
- If a test fails, fix the cause. Do not skip it to go green.
