"""Guards for the checks hassfest and HACS run in CI.

These stay local and do not call GitHub. They fail when a change would make
the publish workflow red for a reason we can see in the tree.
"""

from __future__ import annotations

import ast
import json
from pathlib import Path

from dev.check_github_metadata import valid_topics

ROOT = Path(__file__).resolve().parents[1]
INTEGRATION = ROOT / "custom_components" / "odecet_info"
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"

# Platforms this integration implements. Importing them is not a dependency.
OWN_PLATFORMS = {"button", "sensor"}


def test_manifest_key_order_matches_hassfest() -> None:
    """hassfest requires domain, name, then the remaining keys in alphabetical order."""
    manifest = json.loads((INTEGRATION / "manifest.json").read_text(encoding="utf-8"))
    keys = list(manifest)
    assert keys[:2] == ["domain", "name"]
    assert keys[2:] == sorted(keys[2:])


def test_recorder_is_declared_because_statistics_import_it() -> None:
    """hassfest rejects a component import that is missing from the manifest."""
    manifest = json.loads((INTEGRATION / "manifest.json").read_text(encoding="utf-8"))
    declared = set(manifest.get("dependencies", [])) | set(manifest.get("after_dependencies", []))
    imported = _imported_components()
    missing = imported - OWN_PLATFORMS - declared
    assert not missing, f"Add these to manifest dependencies: {sorted(missing)}"
    assert "recorder" in declared


def test_hacs_brand_icon_is_a_png_inside_the_integration() -> None:
    """HACS looks for custom_components/<domain>/brand/icon.png, not brand/ at the root."""
    icon = INTEGRATION / "brand" / "icon.png"
    assert icon.is_file()
    assert icon.read_bytes().startswith(PNG_MAGIC)


def test_generic_github_topics_do_not_satisfy_hacs() -> None:
    """HACS drops topics such as home-assistant, so the repo needs a specific one."""
    assert valid_topics(["home-assistant", "hacs", "sensor"]) == []
    assert valid_topics(["home-assistant", "water"]) == ["water"]


def test_license_file_stays_identifiable_as_mit() -> None:
    """GitHub reports SPDX NOASSERTION when the MIT text has an extra section."""
    license_text = (ROOT / "LICENSE").read_text(encoding="utf-8")
    assert license_text.startswith("MIT License\n")
    assert "Permission is hereby granted" in license_text
    assert "DISCLAIMER" not in license_text
    notice = (ROOT / "NOTICE").read_text(encoding="utf-8")
    assert "unofficial" in notice.lower()
    assert "odecet.info" in notice


def _imported_components() -> set[str]:
    found: set[str] = set()
    for path in INTEGRATION.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.ImportFrom) or not node.module:
                continue
            prefix = "homeassistant.components."
            if node.module.startswith(prefix):
                found.add(node.module.removeprefix(prefix).split(".", 1)[0])
    return found
