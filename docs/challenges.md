# Challenges

<p align="center">
  <a href="challenges.md"><img alt="English" src="https://img.shields.io/badge/English-1f6feb?style=for-the-badge"></a>
  <a href="cs/challenges.md"><img alt="Čeština" src="https://img.shields.io/badge/%C4%8Ce%C5%A1tina-6e7681?style=for-the-badge"></a>
</p>

## Sign-in is an HTML form, not an API

The sign-in page posts `multipart/form-data` and expects the body `True`. A JSON client would never log in. The same response also has to carry the antiforgery cookie forward. The honeypot field `website` is easy to miss and must be empty.

## CSV export is generated in the browser

The export menu is DataTables `csvHtml5` / `excelHtml5`. There is no CSV URL. Treating "CSV" as a second parser still matters: the integration serializes the table the way the button does, and it will use a real file if the site adds one. `auto` tries that path and falls back to the HTML cells.

## The history looks paged, but it is not

The screenshot shows pages because DataTables pages the browser. The server sends the whole table. Following "next page" links would be the wrong client.

## Heat rows are scale units

Water is labeled `m3`. Heat cells in `Jednotka` are empty, and the page does not show `kWh` or `GJ`. The empty cell is the dimensionless counter of a radiator cost allocator. The integration stores `scale units` and does not put that sensor on the Energy dashboard. A water row with an empty unit still raises a repair. A heat row that really contains `GJ` or `kWh` keeps that energy unit.

`m3` is normalized to `m³` because that is the same unit written without the superscript, not a guess.

## Duplicate rows

The history repeats identical serial, timestamp, and value rows. They collapse to one reading. A decrease is kept, because a meter replacement is valid, and Home Assistant `total_increasing` statistics treat it as a reset.

## The period form is monthly and account-specific

The dashboard form needs the hidden `flat` value from that account's page. The integration reads it and requests the range it needs, then drops days before the user's start date.

## Publish checks

HACS looks for `custom_components/odecet_info/brand/icon.png`. A `brand/` directory at the repository root does not satisfy that check.

GitHub license detection returns SPDX `NOASSERTION` when the MIT text has an extra disclaimer section. HACS then rejects the repository. The disclaimer lives in `NOTICE`. `LICENSE` stays the MIT text.

HACS also ignores generic topics such as `home-assistant` and `hacs`. The repository needs at least one specific topic, such as `water` or `energy`.

## HACS cannot test a commit that is not on GitHub

The pre-push check used to download the integration through HACS. That download is the last commit already on GitHub, so it never saw the change that was about to be pushed. Pre-push testing now copies the working tree into the Home Assistant config. The HACS download runs after the push, and after a release it downloads that release tag.

## HACS wants a GitHub device login

HACS 2 will not create its config entry until someone authorizes it at
`https://github.com/login/device`. The local container has no GitHub session.
The bootstrap stores a HACS entry with an empty token so downloads of this
public repository use the unauthenticated GitHub API. That is enough for one
install. If GitHub answers 403, sign in to HACS from the Home Assistant UI.

The default HACS catalog host (`data-v2.hacs.xyz`) was unreachable from this
container. Adding the repository by its GitHub name does not need that host.

## A meter device must point at an existing account device

Home Assistant rejects `via_device` when the parent device does not exist yet,
and current releases want `via_device_id` instead of the identifier tuple.
The account device is created before the meter sensors, and the link uses
whichever field that Home Assistant version declares.

## Statistics must not be imported twice

Importing an external statistic and also letting the sensor record `total_increasing` would double-count water or heat. History is imported with `async_import_statistics` onto the sensor entity (`source` `recorder`) and only when the unit is known.
