---
name: versioning
description: Bump semver, update the English changelog, and publish a GitHub release. Use when shipping a fix or a user-facing change, and never for a major or release candidate unless the user explicitly approved that version.
---

# Versioning

`version.json` is the source of truth. `custom_components/odecet_info/manifest.json` `version` must equal `version.json` `version`. `channel` is `stable` or `rc`.

Versions follow semantic versioning. Minor and patch numbers may be 10 or higher. Do not invent a cap at 9.

## When to bump

Do not bump for a docs-only, comment-only, or skill-only edit.

Bump once for the release, in the same commit as the code it describes. Do not open a second bump for the same unreleased chunk.

- **Patch** (`0.1.4` to `0.1.5`): a bugfix, CI fix, or parser hardening that does not add a user-facing capability.
- **Minor** (`0.2.0`): a backward-compatible user-facing addition.
- **Major:** do not change the major number, and do not start a release candidate, unless the user explicitly approves that major in the current conversation.
- **Release candidate:** only after the user explicitly says a new major is being prepared. Use `1.0.0-rc.1`, then `1.0.0-rc.2`, and set `channel` to `rc`. Removing `-rc` and publishing the major also requires an explicit yes. Set `channel` back to `stable` on that release.

## Changelog

Update `CHANGELOG.md` in that same commit, without asking. English only. Newest release first. Each release has the version, the date, what changed, and a short why. Follow Keep a Changelog headings (`Added`, `Changed`, `Fixed`, `Removed`) and only include headings that apply.

## Publish

A minor or patch bump is not done until both of these exist:

- an annotated tag `vX.Y.Z` (the `v` prefix is required; the manifest and `version.json` stay without it)
- a GitHub Release on that tag whose body is the changelog section

HACS installs the latest GitHub Release, not `main`. A tag with no release does not count. Do not set `zip_release` in `hacs.json`; HACS can download the tag archive.

A major tag, and the first `rc` tag, wait until the user has approved that version. Do not create them speculatively.

After the release is on GitHub, run `uv run python dev/bootstrap_ha.py --hacs --version vX.Y.Z`.
