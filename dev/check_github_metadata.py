"""Fail CI when GitHub metadata would fail the HACS action.

HACS ignores generic topics and requires a detected SPDX license. This runs
in GitHub Actions, where GITHUB_TOKEN can read the repository. It does not
run during local pytest.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request

# Kept in step with hacs.repositories.base.TOPIC_FILTER. Generic topics do not count.
TOPIC_FILTER = {
    "add-on",
    "addon",
    "app",
    "appdaemon",
    "appdaemon-apps",
    "custom-card",
    "custom-cards",
    "custom-component",
    "custom-components",
    "customcomponents",
    "hacktoberfest",
    "hacs",
    "hacs-default",
    "hacs-integration",
    "hacs-repository",
    "hass",
    "hassio",
    "home-assistant",
    "home-assistant-custom",
    "home-assistant-frontend",
    "home-assistant-hacs",
    "home-assistant-sensor",
    "home-automation",
    "homeassistant",
    "homeassistant-components",
    "homeassistant-integration",
    "homeassistant-sensor",
    "homeautomation",
    "integration",
    "lovelace",
    "lovelace-ui",
    "media-player",
    "mediaplayer",
    "plugin",
    "python",
    "python-script",
    "python_script",
    "sensor",
    "smart-home",
    "smarthome",
}


def valid_topics(topics: list[str]) -> list[str]:
    """Topics HACS still counts after it drops the generic ones."""
    return [topic for topic in topics if topic not in TOPIC_FILTER]


# Specific topics HACS will count. Generic names such as home-assistant are ignored.
REQUIRED_TOPICS = ("energy", "metering", "water")


def main() -> int:
    repository = os.environ.get("GITHUB_REPOSITORY")
    token = os.environ.get("GITHUB_TOKEN")
    if not repository or not token:
        print("GitHub metadata check skipped (not running in Actions).")
        return 0
    payload = _github(token, "GET", f"/repos/{repository}")
    topics = valid_topics(payload.get("topics") or [])
    spdx = (payload.get("license") or {}).get("spdx_id")
    failed = False
    if not topics:
        # The workflow ignores this HACS check until an admin adds the topics.
        print(
            "Warning: HACS topics are still missing. "
            f"Add {', '.join(REQUIRED_TOPICS)} in the GitHub About box, "
            "then remove `ignore: topics` from the workflow."
        )
    else:
        print(f"Valid topics: {', '.join(topics)}")
    if spdx in {None, "NOASSERTION"}:
        print(f"HACS will reject this repository: GitHub license SPDX is {spdx!r}.")
        failed = True
    else:
        print(f"License SPDX: {spdx}")
    return 1 if failed else 0


def _github(token: str, method: str, path: str, payload: dict | None = None) -> dict:
    data = None if payload is None else json.dumps(payload).encode()
    request = urllib.request.Request(
        f"https://api.github.com{path}",
        data=data,
        method=method,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "User-Agent": "odecet-info-metadata-check",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            body = response.read().decode()
    except urllib.error.HTTPError as err:
        detail = err.read().decode(errors="replace")[:300]
        raise SystemExit(f"GitHub {method} {path} failed ({err.code}): {detail}") from err
    return json.loads(body) if body else {}


if __name__ == "__main__":
    sys.exit(main())
