---
name: versioning
description: Bump semver, update both changelogs, and publish a GitHub release. Use when shipping a fix or a user-facing change, and never for a major or release candidate unless the user explicitly approved that version.
---

# Versioning

`version.json` is the source of truth. `custom_components/odecet_info/manifest.json` `version` must equal `version.json` `version`. `channel` is `stable` or `rc`.

Versions follow semantic versioning. Minor and patch numbers may be 10 or higher. Do not invent a cap at 9.

## When to bump

Do not bump for a docs-only, comment-only, or skill-only edit.

Bump once for the release, in the same commit as the code it describes. Do not open a second bump for the same unreleased chunk. Several patches in one day are normal. When the choice is unclear, use a patch.

- **Patch** (`0.3.0` to `0.3.1`): a fix, wording, translation, display name, docs shipped with that change, CI, or parser hardening. A label the user can see is not a new capability.
- **Minor** (`0.3.1` to `0.4.0`) only when the user can do something new, or an existing sensor changes what it reports. Something new is a new entity, option, medium, or statistic. A meaning change is what 0.3.0 did: an empty heat unit became `scale units` and left the Energy dashboard. The changelog must name that capability or that meaning change in one sentence. If you cannot name one, it is a patch.
- **Major:** do not change the major number, and do not start a release candidate, unless the user explicitly approves that major in the current conversation.
- **Release candidate:** only after the user explicitly says a new major is being prepared. Use `1.0.0-rc.1`, then `1.0.0-rc.2`, and set `channel` to `rc`. Removing `-rc` and publishing the major also requires an explicit yes. Set `channel` back to `stable` on that release.

## Changelog

Update `CHANGELOG.md` and `docs/cs/CHANGELOG.md` in that same commit, without asking. Newest release first. Each release has the version, the date, what changed, and a short why. Follow Keep a Changelog headings (`Added`, `Changed`, `Fixed`, `Removed`) and only include headings that apply.

## Publish

A minor or patch bump is not done until the annotated tag `vX.Y.Z` is on GitHub. The `v` prefix is required. The manifest and `version.json` stay without it.

Pushing that tag runs `.github/workflows/release.yml`. The workflow reads the matching `CHANGELOG.md` section and creates or updates the GitHub Release with `make_latest` true. Do not publish the release by hand, and do not leave the previous release marked latest. A tag that contains `-rc` is not published.

HACS installs the latest GitHub Release, not `main`. A tag with no release does not count. Do not set `zip_release` in `hacs.json`; HACS can download the tag archive.

A major tag, and the first `rc` tag, wait until the user has approved that version. Do not create them speculatively.

After the release is on GitHub, run `uv run python dev/bootstrap_ha.py --hacs --version vX.Y.Z`.
