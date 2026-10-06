"""Install this integration through HACS into the local Home Assistant container.

Reads `.env` for the odecet.info account. Prints status lines only.
Does not print the account password, the Home Assistant token, or cookies.
"""

from __future__ import annotations

import asyncio
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = "http://127.0.0.1:8123"
CLIENT_ID = "http://127.0.0.1:8123/"
HA_USERNAME = "dev"
HA_PASSWORD = "dev"
REPOSITORY = "JustGetSchwifty/odecet-info-ha-integration"


def load_env() -> dict[str, str]:
    values: dict[str, str] = {}
    for raw in (ROOT / ".env").read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def request(
    method: str,
    path: str,
    payload: dict | None = None,
    token: str | None = None,
    form: dict[str, str] | None = None,
) -> tuple[int, dict | str]:
    data: bytes | None = None
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if form is not None:
        data = urllib.parse.urlencode(form).encode()
        headers["Content-Type"] = "application/x-www-form-urlencoded"
    elif payload is not None:
        data = json.dumps(payload).encode()
    req = urllib.request.Request(BASE + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            body = response.read().decode()
            status = response.status
    except urllib.error.HTTPError as err:
        body = err.read().decode()
        status = err.code
    if not body:
        return status, ""
    try:
        return status, json.loads(body)
    except json.JSONDecodeError:
        return status, body


def wait_until_up(seconds: int = 180) -> None:
    deadline = time.time() + seconds
    while time.time() < deadline:
        try:
            status, _body = request("GET", "/api/")
            if status in {200, 401}:
                print("Home Assistant is answering")
                return
        except (urllib.error.URLError, TimeoutError):
            pass
        time.sleep(3)
    raise SystemExit("Home Assistant did not start")


def onboard() -> str:
    status, body = request("GET", "/api/onboarding")
    print(f"onboarding status {status}")
    steps = body if isinstance(body, list) else []
    done = {item["step"] for item in steps if isinstance(item, dict) and item.get("done")}
    token = ""
    if "user" not in done:
        status, created = request(
            "POST",
            "/api/onboarding/users",
            {
                "name": "Dev",
                "username": HA_USERNAME,
                "password": HA_PASSWORD,
                "client_id": CLIENT_ID,
                "language": "en",
            },
        )
        if status != 200 or not isinstance(created, dict):
            raise SystemExit(f"Could not create the local user ({status})")
        token = exchange(created["auth_code"])
        print("created local user")
    else:
        token = login()
        print("local user already exists")
    for path, payload in (
        ("/api/onboarding/core_config", {}),
        ("/api/onboarding/analytics", {}),
        ("/api/onboarding/integration", {"client_id": CLIENT_ID, "redirect_uri": CLIENT_ID}),
    ):
        status, _body = request("POST", path, payload, token=token)
        print(f"POST {path} -> {status}")
    return token


def exchange(code: str) -> str:
    status, body = request(
        "POST",
        "/auth/token",
        form={
            "grant_type": "authorization_code",
            "code": code,
            "client_id": CLIENT_ID,
        },
    )
    if status != 200 or not isinstance(body, dict) or "access_token" not in body:
        raise SystemExit(f"Token exchange failed ({status})")
    return body["access_token"]


def login() -> str:
    status, started = request(
        "POST",
        "/auth/login_flow",
        {
            "client_id": CLIENT_ID,
            "handler": ["homeassistant", None],
            "redirect_uri": CLIENT_ID,
        },
    )
    if not isinstance(started, dict):
        raise SystemExit(f"Login flow did not start ({status})")
    status, finished = request(
        "POST",
        f"/auth/login_flow/{started['flow_id']}",
        {
            "client_id": CLIENT_ID,
            "username": HA_USERNAME,
            "password": HA_PASSWORD,
        },
    )
    if not isinstance(finished, dict) or finished.get("type") != "create_entry":
        raise SystemExit(f"Local login failed ({status})")
    return exchange(finished["result"])


def start_flow(token: str, handler: str) -> dict:
    status, body = request(
        "POST",
        "/api/config/config_entries/flow",
        {"handler": handler, "show_advanced_options": True},
        token=token,
    )
    if not isinstance(body, dict):
        raise SystemExit(f"Could not start {handler} flow ({status})")
    print(f"{handler} flow -> {body.get('type')} step={body.get('step_id')}")
    return body


def configure(token: str, flow_id: str, data: dict) -> dict:
    status, body = request(
        "POST",
        f"/api/config/config_entries/flow/{flow_id}",
        data,
        token=token,
    )
    if not isinstance(body, dict):
        raise SystemExit(f"Flow configure failed ({status}) {body!s:.200}")
    print(f"configure -> {body.get('type')} step={body.get('step_id')} reason={body.get('reason')}")
    return body


def setup_hacs(token: str) -> None:
    entries = request("GET", "/api/config/config_entries/entry", token=token)[1]
    if isinstance(entries, list) and any(item.get("domain") == "hacs" for item in entries):
        print("HACS config entry already exists")
        return
    flow = start_flow(token, "hacs")
    if flow.get("type") == "form" and flow.get("step_id") == "user":
        flow = configure(
            token,
            flow["flow_id"],
            {
                "acc_logs": True,
                "acc_addons": True,
                "acc_untested": True,
                "acc_disable": True,
            },
        )
    if flow.get("type") == "progress":
        placeholders = flow.get("description_placeholders") or {}
        code = placeholders.get("code", "")
        print("HACS is waiting for GitHub device authorization.")
        print(f"Open https://github.com/login/device and enter code {code}")
        raise SystemExit(2)
    if flow.get("type") != "create_entry":
        raise SystemExit(f"HACS setup stopped at {flow.get('type')} {flow.get('reason')}")
    print("HACS config entry created")


def install_repository(token: str) -> None:
    """Add the GitHub repository and download it. HACS acks adds even when they fail."""
    status, added = websocket(
        token,
        "hacs/repositories/add",
        repository=REPOSITORY,
        category="integration",
    )
    print(f"hacs add -> {status} {added}")
    deadline = time.time() + 90
    repo_id = None
    while time.time() < deadline:
        _status, listing = websocket(token, "hacs/repositories/list")
        repos = listing if isinstance(listing, list) else []
        match = next((item for item in repos if item.get("full_name") == REPOSITORY), None)
        if match:
            repo_id = str(match["id"])
            print(f"repository registered id={repo_id} installed={match.get('installed')}")
            if match.get("installed"):
                return
            break
        time.sleep(3)
    if repo_id is None:
        raise SystemExit("HACS did not register the repository")
    status, downloaded = websocket(token, "hacs/repository/download", repository=repo_id)
    print(f"hacs download -> {status} {downloaded}")
    if isinstance(downloaded, dict) and downloaded.get("success") is False:
        raise SystemExit("HACS download failed")


def websocket(token: str, command: str, **fields: object) -> tuple[str, object]:
    import aiohttp

    async def _call() -> tuple[str, object]:
        async with aiohttp.ClientSession() as session:
            async with session.ws_connect(BASE.replace("http", "ws") + "/api/websocket") as ws:
                await ws.receive_json()
                await ws.send_json({"type": "auth", "access_token": token})
                auth = await ws.receive_json()
                if auth.get("type") != "auth_ok":
                    raise SystemExit("WebSocket auth failed")
                await ws.send_json({"id": 1, "type": command, **fields})
                while True:
                    message = await ws.receive_json()
                    if message.get("id") == 1:
                        return message.get("type", ""), message.get("result", message)

    return asyncio.run(_call())


def setup_integration(token: str, env: dict[str, str]) -> None:
    flow = start_flow(token, "odecet_info")
    if flow.get("type") != "form":
        raise SystemExit("Odecet.info flow did not open")
    flow = configure(
        token,
        flow["flow_id"],
        {
            "username": env["ODECET_INFO_USERNAME"],
            "password": env["ODECET_INFO_PASSWORD"],
            "signin_url": env["ODECET_INFO_SIGNIN_URL"],
        },
    )
    if flow.get("type") == "abort":
        raise SystemExit(f"Integration setup aborted: {flow.get('reason')}")
    if flow.get("step_id") != "meters":
        errors = flow.get("errors")
        raise SystemExit(f"Sign-in step did not advance ({flow.get('type')} {errors})")
    mediums = _medium_values(flow)
    if not mediums:
        raise SystemExit("No meter types were offered")
    print(f"offering mediums: {', '.join(mediums)}")
    flow = configure(
        token,
        flow["flow_id"],
        {"mediums": mediums, "fetch_method": "auto"},
    )
    if flow.get("type") != "create_entry":
        raise SystemExit(f"Could not create the integration entry ({flow.get('reason')})")
    print("integration config entry created")


def _medium_values(flow: dict) -> list[str]:
    for field in flow.get("data_schema") or []:
        if field.get("name") != "mediums":
            continue
        selector = field.get("selector", {}).get("select", {})
        options = selector.get("options") or []
        values = []
        for option in options:
            if isinstance(option, dict):
                values.append(option["value"])
            else:
                values.append(option)
        return values
    return ["cold_water", "hot_water", "heat"]


def wait_for_readings(token: str) -> None:
    deadline = time.time() + 180
    while time.time() < deadline:
        status, states = request("GET", "/api/states", token=token)
        if status == 200 and isinstance(states, list):
            readings = [
                item
                for item in states
                if item.get("entity_id", "").startswith("sensor.")
                and item["entity_id"].endswith("_reading")
            ]
            numeric = []
            for item in readings:
                try:
                    float(item.get("state", ""))
                except ValueError:
                    continue
                numeric.append(item)
            print(f"reading sensors={len(readings)} numeric={len(numeric)}")
            if numeric:
                for item in numeric:
                    unit = item.get("attributes", {}).get("unit_of_measurement", "")
                    print(f"  {item['entity_id']} = {item['state']} {unit}")
                return
        time.sleep(5)
    raise SystemExit("Meter sensors did not get a numeric state")


def restart(token: str) -> str:
    request("POST", "/api/services/homeassistant/restart", {}, token=token)
    print("restart requested")
    time.sleep(8)
    wait_until_up()
    return login()


def main() -> None:
    env = load_env()
    wait_until_up()
    token = onboard()
    setup_hacs(token)
    install_repository(token)
    token = restart(token)
    setup_integration(token, env)
    wait_for_readings(token)
    print("Local Home Assistant is ready at http://127.0.0.1:8123")
    print("Local login: dev / dev")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)
