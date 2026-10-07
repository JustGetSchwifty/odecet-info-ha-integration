"""Guards for the checks hassfest and HACS run in CI.

These stay local and do not call GitHub. They fail when a change would make
the publish workflow red for a reason we can see in the tree.
"""

from __future__ import annotations

import ast
import json
import os
import re
from pathlib import Path

from dev.check_github_metadata import valid_topics

ROOT = Path(__file__).resolve().parents[1]
INTEGRATION = ROOT / "custom_components" / "odecet_info"
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"

# Platforms this integration implements. Importing them is not a dependency.
OWN_PLATFORMS = {"button", "sensor"}


def test_manifest_version_matches_version_json() -> None:
    """HACS and the changelog must describe the same version."""
    manifest = json.loads((INTEGRATION / "manifest.json").read_text(encoding="utf-8"))
    recorded = json.loads((ROOT / "version.json").read_text(encoding="utf-8"))
    assert manifest["version"] == recorded["version"]
    assert recorded["channel"] in {"stable", "rc"}
    if recorded["channel"] == "rc":
        assert "-rc." in recorded["version"]
    else:
        assert "-rc." not in recorded["version"]


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
    assert _png_size(icon) == (256, 256)
    assert _png_size(INTEGRATION / "brand" / "icon@2x.png") == (512, 512)
    assert _png_size(INTEGRATION / "brand" / "logo.png") == (512, 170)
    assert _png_size(INTEGRATION / "brand" / "logo@2x.png") == (1024, 341)


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


def _png_size(path: Path) -> tuple[int, int]:
    import struct

    header = path.read_bytes()[:24]
    assert header.startswith(PNG_MAGIC)
    width, height = struct.unpack(">II", header[16:24])
    return width, height


QUALITY_RULES = {
    "action-exceptions",
    "action-setup",
    "appropriate-polling",
    "async-dependency",
    "brands",
    "common-modules",
    "config-entry-unloading",
    "config-flow",
    "config-flow-test-coverage",
    "dependency-transparency",
    "devices",
    "diagnostics",
    "discovery",
    "discovery-update-info",
    "docs-actions",
    "docs-conditions",
    "docs-configuration-parameters",
    "docs-data-update",
    "docs-examples",
    "docs-high-level-description",
    "docs-installation-instructions",
    "docs-installation-parameters",
    "docs-known-limitations",
    "docs-removal-instructions",
    "docs-supported-devices",
    "docs-supported-functions",
    "docs-triggers",
    "docs-troubleshooting",
    "docs-use-cases",
    "dynamic-devices",
    "entity-category",
    "entity-device-class",
    "entity-disabled-by-default",
    "entity-event-setup",
    "entity-translations",
    "entity-unavailable",
    "entity-unique-id",
    "exception-translations",
    "has-entity-name",
    "icon-translations",
    "inject-websession",
    "integration-owner",
    "log-when-unavailable",
    "parallel-updates",
    "reauthentication-flow",
    "reconfiguration-flow",
    "repair-issues",
    "runtime-data",
    "stale-devices",
    "strict-typing",
    "test-before-configure",
    "test-before-setup",
    "test-coverage",
    "unique-config-entry",
}


_PLACEHOLDER = re.compile(r"\{([a-zA-Z0-9_]+)\}")


def _english_docs() -> list[Path]:
    pages = [ROOT / "README.md", ROOT / "CHANGELOG.md"]
    pages.extend(sorted((ROOT / "docs").glob("*.md")))
    return pages


def _czech_doc(english: Path) -> Path:
    return ROOT / "docs" / "cs" / english.name


def _headings(text: str) -> int:
    return sum(1 for line in text.splitlines() if line.startswith("#"))


def test_user_docs_have_a_czech_twin() -> None:
    """Every English user page has a Czech twin, and each page links to the other."""
    for english in _english_docs():
        czech = _czech_doc(english)
        assert czech.is_file(), czech
        english_text = english.read_text(encoding="utf-8")
        czech_text = czech.read_text(encoding="utf-8")
        assert _headings(czech_text) >= _headings(english_text), czech
        for page, other in ((english, czech), (czech, english)):
            text = page.read_text(encoding="utf-8")
            first = text.lstrip().splitlines()[0]
            assert "English" in first and "Čeština" in first, page
            relative = Path(os.path.relpath(other, page.parent)).as_posix()
            assert f"]({relative})" in text, page
    heat_en = (ROOT / "docs" / "heat-cost-allocation.md").read_text(encoding="utf-8")
    heat_cs = (ROOT / "docs" / "cs" / "heat-cost-allocation.md").read_text(encoding="utf-8")
    assert "$$" in heat_en and "$$" in heat_cs
    assert "scale unit" in heat_en.casefold()
    assert "dílek" in heat_cs.casefold()


def _leaf_strings(value: object, prefix: str = "") -> dict[str, str]:
    if isinstance(value, dict):
        leaves: dict[str, str] = {}
        for key, item in value.items():
            path = f"{prefix}.{key}" if prefix else key
            leaves.update(_leaf_strings(item, path))
        return leaves
    if isinstance(value, str):
        return {prefix: value}
    return {}


def test_czech_translations_cover_every_english_string() -> None:
    """A new English UI string is not done until the Czech file has the same key."""
    english = json.loads((INTEGRATION / "strings.json").read_text(encoding="utf-8"))
    czech = json.loads((INTEGRATION / "translations" / "cs.json").read_text(encoding="utf-8"))
    english_leaves = _leaf_strings(english)
    czech_leaves = _leaf_strings(czech)
    missing = sorted(set(english_leaves) - set(czech_leaves))
    assert not missing, missing
    for key, text in english_leaves.items():
        assert set(_PLACEHOLDER.findall(text)) == set(_PLACEHOLDER.findall(czech_leaves[key])), key


def test_english_translations_match_strings() -> None:
    """Home Assistant loads translations/en.json. strings.json must stay a copy."""
    strings = (INTEGRATION / "strings.json").read_text(encoding="utf-8")
    english = (INTEGRATION / "translations" / "en.json").read_text(encoding="utf-8")
    assert english == strings


def test_quality_scale_lists_every_published_rule() -> None:
    """A rule is done, or exempt with a reason. The file cannot drift from the scale."""
    import yaml

    recorded = yaml.safe_load((INTEGRATION / "quality_scale.yaml").read_text(encoding="utf-8"))
    rules = recorded["rules"]
    assert set(rules) == QUALITY_RULES
    for name, value in rules.items():
        if value == "done":
            continue
        assert value["status"] == "exempt", name
        assert value.get("comment"), name


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
