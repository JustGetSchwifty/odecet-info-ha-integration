# Changelog

All notable changes to this project are documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html). Patch and minor numbers are not limited to a single digit.

Nothing was tagged before this release, so the work that landed on `main` is recorded once, as 0.1.4, instead of as invented intermediate versions.

## [0.1.4] - 2026-10-07

First recorded release of the unofficial odecet.info integration.

### Added

- Home Assistant config flow for an odecet.info account, with a choice of the meter types the account actually has.
- Parsers for the history table and for the CSV export the site builds in the browser.
- One register sensor per meter, a manual sync button, and a one-minute cooldown shown as the next allowed sync time.
- A daily background sync with jitter and a capped retry. Heat meters that arrive without a unit stay off statistics and raise a repair.
- Local Home Assistant check that copies the working tree before a push, because HACS can only download a commit that is already on GitHub.
- CI for pytest, hassfest, and HACS, plus README badges for that status and for the published release.

### Why

Users need a version they can install through HACS. Recording one 0.1.4 avoids pretending that 0.1.1 through 0.1.3 were released.

[0.1.4]: https://github.com/JustGetSchwifty/odecet-info-ha-integration/releases/tag/v0.1.4
