"""Inspect an odecet.info account without Home Assistant.

Reads `.env`. Prints meter summaries and can write JSON or CSV. Never prints
the password, the email, or session cookies.
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import io
import json
import sys
from pathlib import Path

import aiohttp

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from custom_components.odecet_info.client import OdecetClient  # noqa: E402
from custom_components.odecet_info.errors import OdecetError  # noqa: E402
from custom_components.odecet_info.models import FetchMethod, ReadingSet  # noqa: E402

ENV_PATH = ROOT / ".env"


def load_env(path: Path) -> dict[str, str]:
    """Parse a simple KEY=VALUE file. Values are not logged."""
    values: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def summarize(parsed: ReadingSet) -> list[dict[str, object]]:
    """One row per meter, with the span of its readings."""
    rows: list[dict[str, object]] = []
    for meter in parsed.meters():
        rows.append(
            {
                "medium": meter.medium.value,
                "serial": meter.serial,
                "unit": meter.unit,
                "readings": len(meter.readings),
                "oldest_at": meter.readings[0].timestamp.isoformat(),
                "newest_at": meter.latest.timestamp.isoformat(),
                "latest": str(meter.latest.value),
            }
        )
    return rows


def readings_as_json(parsed: ReadingSet) -> str:
    """Readings as JSON. Issues are included. Credentials are not."""
    payload = {
        "source": parsed.source,
        "meters": summarize(parsed),
        "readings": [
            {
                "medium": reading.medium.value,
                "serial": reading.serial,
                "timestamp": reading.timestamp.isoformat(),
                "value": str(reading.value),
                "unit": reading.unit,
            }
            for reading in parsed.readings
        ],
        "issues": [
            {"code": issue.code, "message": issue.message, "serial": issue.serial}
            for issue in parsed.issues
        ],
    }
    return json.dumps(payload, indent=2)


def readings_as_csv(parsed: ReadingSet) -> str:
    """One CSV row per reading."""
    buffer = io.StringIO()
    writer = csv.DictWriter(
        buffer,
        fieldnames=["medium", "serial", "timestamp", "value", "unit"],
        lineterminator="\n",
    )
    writer.writeheader()
    for reading in parsed.readings:
        writer.writerow(
            {
                "medium": reading.medium.value,
                "serial": reading.serial,
                "timestamp": reading.timestamp.isoformat(),
                "value": str(reading.value),
                "unit": reading.unit or "",
            }
        )
    return buffer.getvalue()


def print_summary(parsed: ReadingSet) -> None:
    """Print one line per meter. No account secrets."""
    print(f"source={parsed.source} readings={len(parsed.readings)} issues={len(parsed.issues)}")
    for row in summarize(parsed):
        unit = row["unit"] or "(none)"
        print(
            f"{row['medium']} {row['serial']} unit={unit} "
            f"readings={row['readings']} {row['oldest_at']} .. {row['newest_at']}"
        )


async def login(env: dict[str, str]) -> int:
    """Check sign-in. Print success or the error type."""
    async with aiohttp.ClientSession() as session:
        client = OdecetClient(
            session,
            env["ODECET_INFO_SIGNIN_URL"],
            env["ODECET_INFO_USERNAME"],
            env["ODECET_INFO_PASSWORD"],
        )
        try:
            await client.async_login()
        except OdecetError as err:
            print(f"login failed: {type(err).__name__}")
            return 1
    print("login ok")
    return 0


async def fetch(env: dict[str, str], args: argparse.Namespace) -> int:
    """Download with the integration client and optionally write files."""
    from datetime import date

    sync_from = date.fromisoformat(args.sync_from) if args.sync_from else None
    async with aiohttp.ClientSession() as session:
        client = OdecetClient(
            session,
            env["ODECET_INFO_SIGNIN_URL"],
            env["ODECET_INFO_USERNAME"],
            env["ODECET_INFO_PASSWORD"],
        )
        try:
            parsed = await client.async_fetch(FetchMethod(args.method), sync_from)
        except OdecetError as err:
            print(f"fetch failed: {type(err).__name__}")
            return 1
    print_summary(parsed)
    if args.json:
        Path(args.json).write_text(readings_as_json(parsed), encoding="utf-8")
        print(f"wrote {args.json}")
    if args.csv:
        Path(args.csv).write_text(readings_as_csv(parsed), encoding="utf-8")
        print(f"wrote {args.csv}")
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("login", help="Check that the .env account can sign in")
    fetch_parser = sub.add_parser("fetch", help="Download readings and print their span")
    fetch_parser.add_argument("--method", choices=["auto", "csv", "table"], default="auto")
    fetch_parser.add_argument("--sync-from", help="Ignore readings before this YYYY-MM-DD date")
    fetch_parser.add_argument("--json", help="Write the readings to this JSON file")
    fetch_parser.add_argument("--csv", help="Write one row per reading to this CSV file")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    env = load_env(ENV_PATH)
    if args.command == "login":
        return asyncio.run(login(env))
    return asyncio.run(fetch(env, args))


if __name__ == "__main__":
    raise SystemExit(main())
