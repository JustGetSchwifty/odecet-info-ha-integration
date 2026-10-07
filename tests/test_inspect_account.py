"""The local inspection command. The session is scripted."""

from datetime import datetime
from zoneinfo import ZoneInfo

import pytest
from custom_components.odecet_info.client import OdecetClient
from custom_components.odecet_info.models import FetchMethod
from dev.inspect_account import parse_args, readings_as_csv, readings_as_json, summarize
from tests.fakes import Response, ScriptedSession, load_fixture

NOW = datetime(2026, 10, 6, 12, tzinfo=ZoneInfo("Europe/Prague"))
SIGNIN = "https://odecet.info/signin"


def _session() -> ScriptedSession:
    pages = (
        (200, load_fixture("signin.html")),
        (200, "True"),
        (200, load_fixture("dashboard.html")),
        (200, load_fixture("dashboard.html")),
    )
    return ScriptedSession([Response(status, body, SIGNIN) for status, body in pages])


@pytest.mark.asyncio
@pytest.mark.parametrize("method", [FetchMethod.AUTO, FetchMethod.CSV, FetchMethod.TABLE])
async def test_fetch_methods_summarize_without_the_password(method: FetchMethod) -> None:
    parsed = await OdecetClient(_session(), SIGNIN, "user@example.com", "secret-value").async_fetch(
        method, now=NOW
    )
    summary = summarize(parsed)
    assert summary
    assert all(row["serial"] for row in summary)
    exported = readings_as_json(parsed) + readings_as_csv(parsed)
    assert "1001" in exported
    assert "secret-value" not in exported
    assert "user@example.com" not in exported


def test_parse_args_accepts_outputs() -> None:
    args = parse_args(
        ["fetch", "--method", "csv", "--sync-from", "2024-01-01", "--json", "out.json"]
    )
    assert args.command == "fetch"
    assert args.method == "csv"
    assert args.sync_from == "2024-01-01"
    assert args.json == "out.json"
