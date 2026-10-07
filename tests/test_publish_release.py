"""The release script extracts a changelog section and refuses a release candidate."""

import pytest
from dev.publish_release import changelog_section, publish


def test_changelog_section_is_only_that_version() -> None:
    notes = changelog_section("0.1.4")
    assert notes.startswith("## [0.1.4]")
    assert "## [0.2.0]" not in notes
    assert "password" not in notes.lower()


def test_release_candidate_tags_are_refused(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GH_TOKEN", "unused")
    monkeypatch.setenv("GITHUB_REPOSITORY", "example/example")
    with pytest.raises(SystemExit):
        publish("v1.0.0-rc.1")
