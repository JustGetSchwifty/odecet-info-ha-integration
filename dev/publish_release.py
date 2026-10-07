"""Create or update the GitHub Release for a tag and mark it latest.

The tag is vX.Y.Z. The release body is that version's section in CHANGELOG.md.
A tag that contains -rc is refused. The workflow does not call this for those.
"""

from __future__ import annotations

import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def changelog_section(version: str) -> str:
    """Return the Keep a Changelog section for version, without the link footer."""
    text = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    match = re.search(
        rf"^## \[{re.escape(version)}\].*?(?=^## \[|\Z)",
        text,
        flags=re.M | re.S,
    )
    if match is None:
        raise SystemExit(f"CHANGELOG.md has no section for {version}")
    return match.group(0).strip() + "\n"


def publish(tag: str) -> None:
    if not tag.startswith("v") or "-rc" in tag:
        raise SystemExit(f"Refusing to publish {tag}")
    version = tag[1:]
    notes = changelog_section(version)
    token = os.environ["GH_TOKEN"]
    repository = os.environ["GITHUB_REPOSITORY"]
    payload = {
        "tag_name": tag,
        "name": tag,
        "body": notes,
        "draft": False,
        "prerelease": False,
        "make_latest": "true",
        "target_commitish": "main",
    }
    request = urllib.request.Request(
        f"https://api.github.com/repos/{repository}/releases",
        data=json.dumps(payload).encode(),
        method="POST",
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "User-Agent": "odecet-info-release",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            created = json.load(response)
    except urllib.error.HTTPError as err:
        if err.code != 422:
            detail = err.read().decode(errors="replace")[:300]
            raise SystemExit(f"GitHub create release failed ({err.code}): {detail}") from err
        created = _update_existing(repository, token, tag, notes)
    print(created["html_url"])


def _update_existing(repository: str, token: str, tag: str, notes: str) -> dict:
    listing = urllib.request.Request(
        f"https://api.github.com/repos/{repository}/releases/tags/{tag}",
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "User-Agent": "odecet-info-release",
        },
    )
    with urllib.request.urlopen(listing, timeout=30) as response:
        current = json.load(response)
    request = urllib.request.Request(
        f"https://api.github.com/repos/{repository}/releases/{current['id']}",
        data=json.dumps(
            {"body": notes, "draft": False, "prerelease": False, "make_latest": "true"}
        ).encode(),
        method="PATCH",
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "User-Agent": "odecet-info-release",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


if __name__ == "__main__":
    publish(sys.argv[1])
