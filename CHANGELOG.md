# Changelog

<p align="center">
  <a href="CHANGELOG.md"><img alt="English" src="https://img.shields.io/badge/English-1f6feb?style=for-the-badge"></a>
  <a href="docs/cs/CHANGELOG.md"><img alt="Čeština" src="https://img.shields.io/badge/%C4%8Ce%C5%A1tina-6e7681?style=for-the-badge"></a>
</p>

All notable changes to this project are documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html). Patch and minor numbers are not limited to a single digit.

Nothing was tagged before this release, so the work that landed on `main` is recorded once, as 0.1.4, instead of as invented intermediate versions.

## [0.3.1] - 2026-10-07

Meter names and the setup form follow the Home Assistant language. The reported values do not change.

### Changed

- A meter device is named `Heat [S/N 39584888]` in English and `Teplo [číslo 39584888]` in Czech. Cold water and hot water use the same pattern.
- The meter and history dropdowns, and the sentence about types the account does not have, use the Czech labels when Home Assistant is in Czech.
- Every user document has a Czech twin, and the first line of each page links to the other language.

### Why

The device name and several setup labels stayed English on a Czech Home Assistant. That is a label change, so it stays on 0.3.

## [0.3.0] - 2026-10-07

An empty heat unit is the raw counter of a radiator cost allocator, not a missing energy unit.

### Changed

- Heat with an empty unit is stored as `scale units`. It stays off the Energy dashboard. The missing-unit repair is no longer raised for that case.
- The meter step warns that heat is often not worth selecting and links the explanation.
- User-facing pages have a Czech twin under `docs/cs/`.

### Why

The site never prints GJ or kWh for those rows. Treating the blank as an error hid a dimensionless scale unit and asked people to fix something the page does not contain.

## [0.2.1] - 2026-10-07

The history graph on the entity shows states recorded since the meter was added. Older registers were already imported as statistics, and that was easy to miss.

### Added

- Diagnostics now include the oldest reading, the newest reading, and how many hourly statistic points were imported.
- `dev/inspect_account.py` signs in with `.env` and can write the readings as JSON or CSV.
- A tag `v*` publishes its changelog section as the latest GitHub Release.
- Green Dependabot pull requests are squash-merged. Pull requests from anyone else are left alone.

### Why

A one-day history graph looked like the download had no past. The span is now visible, and releases and dependency updates no longer wait on a manual click.

## [0.2.0] - 2026-10-07

The integration now follows the published Home Assistant quality-scale rules through platinum, as far as a website login allows.

### Added

- A dedicated sign-in session, so the account cookies are not attached to other integrations.
- Translated entity names, a sync icon, and translated errors.
- Removal of a meter device when that meter disappears from the account.
- README install steps that match the current HACS flow, the brand banner, and a My Home Assistant link.
- Nightly hassfest and HACS validation, strict type checking, and a 95 percent coverage gate.
- Dependabot for Python and GitHub Actions. The floating hassfest and HACS action refs stay unpinned.

### Why

Users get a more reliable install and a codebase that can be checked against the quality scale. Home Assistant does not grade custom integrations, so the platinum mark is this project's own assessment. The login still reads the website, so the integration stays a custom component.

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

[0.3.1]: https://github.com/JustGetSchwifty/odecet-info-ha-integration/releases/tag/v0.3.1
[0.3.0]: https://github.com/JustGetSchwifty/odecet-info-ha-integration/releases/tag/v0.3.0
[0.2.1]: https://github.com/JustGetSchwifty/odecet-info-ha-integration/releases/tag/v0.2.1
[0.2.0]: https://github.com/JustGetSchwifty/odecet-info-ha-integration/releases/tag/v0.2.0
[0.1.4]: https://github.com/JustGetSchwifty/odecet-info-ha-integration/releases/tag/v0.1.4
