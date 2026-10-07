# Odecet.info for Home Assistant

[![English](https://img.shields.io/badge/English-1f6feb?style=for-the-badge)](README.md) [![Čeština](https://img.shields.io/badge/Čeština-6e7681?style=for-the-badge)](docs/cs/README.md)

<img src="https://raw.githubusercontent.com/JustGetSchwifty/odecet-info-ha-integration/main/custom_components/odecet_info/brand/logo@2x.png" alt="odecet.info" width="512">

[![CI](https://github.com/JustGetSchwifty/odecet-info-ha-integration/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/JustGetSchwifty/odecet-info-ha-integration/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/JustGetSchwifty/odecet-info-ha-integration?display_name=tag)](https://github.com/JustGetSchwifty/odecet-info-ha-integration/releases)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Home Assistant](https://img.shields.io/badge/Home%20Assistant-2025.11%2B-blue)](https://www.home-assistant.io/)
[![Stars](https://img.shields.io/github/stars/JustGetSchwifty/odecet-info-ha-integration)](https://github.com/JustGetSchwifty/odecet-info-ha-integration/stargazers)

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=JustGetSchwifty&repository=odecet-info-ha-integration&category=integration)

odecet.info is a Czech website where a household account can read the history of its cold-water, hot-water, and heat meters. This unofficial integration signs in with that account and brings each meter's register into Home Assistant. It is not affiliated with odecet.info or the site's operator. The site can change or block access at any time. See [LICENSE](LICENSE) and [NOTICE](NOTICE).

User documentation and the Home Assistant screens are kept in English and Czech together. A change to one language is not done until the other language has the same change.

The integration follows the published [Home Assistant quality scale](https://developers.home-assistant.io/docs/core/integration-quality-scale/) rules through platinum, with the exemptions recorded in `custom_components/odecet_info/quality_scale.yaml`. Home Assistant does not review custom integrations, so that mark is our assessment against those rules, not a grade from the core team.

## Supported meters

A meter is supported when the signed-in account returns it. There is no separate hardware list.

- Cold water (Studená voda). A unit labeled `m3` is stored as cubic metres.
- Hot water (Teplá voda). Stored the same way.
- Heat (Teplo). The site leaves the unit empty because the number is a dimensionless **scale unit** from a radiator cost allocator, not kilowatt-hours. It is often not worth selecting. [What the heat reading is](docs/heat-cost-allocation.md).

A meter that later disappears from the account is removed from Home Assistant.

## What you get

- One device per meter, linked to an account device. The device is named `Heat [S/N 39584888]` in English. Czech Home Assistant shows `Teplo [číslo 39584888]`. Cold water and hot water use the same pattern.
- A **Reading** sensor with the latest register. In Czech the sensor is **Stav**.
- A **Sync now** button on the account device.
- A **Next manual sync** sensor that shows when that button is allowed again.
- Imported history for sensors whose unit is known, so water can be added to the Energy dashboard.

## How readings are updated

The integration reads the site once a day, at about 04:00 local time, plus a random delay of up to 30 minutes. It does not poll every minute. A failed read retries with backoff and never more often than once a minute. After five failures it opens a repair and waits until the next day. **Sync now** uses the same one-minute limit.

The number on the sensor is the latest register. The history graph on the entity page draws the states Home Assistant has seen since the entity was created, and that graph opens on about the last day. Older registers are stored as hourly long-term statistics. The Energy dashboard, and a statistics graph whose period is an hour or longer, read that series. Diagnostics list `oldest_at`, `latest_at`, and `statistic_points` for each meter, which is the span that was imported. Heat scale units are included in that span. They are still not energy.

## Install

The integration is not in the default HACS catalog. Home Assistant must be **2025.11.0** or newer. HACS refuses the release on an older version.

1. Install [HACS](https://www.hacs.xyz/docs/use/download/download/) and finish its setup, including the GitHub device login, so HACS appears in the sidebar.
2. Open HACS. In the top-right menu, choose **Custom repositories**.
3. Add `https://github.com/JustGetSchwifty/odecet-info-ha-integration`, set the type to **Integration**, and press **Add**. Adding the address does not download the integration.
4. Search for **Odecet.info**, open it, and press **Download**. Leave the newest release selected.
5. Restart Home Assistant if HACS shows **Pending restart**. An update needs that restart. The first download is often loaded without one.
6. Go to **Settings → Devices & services → Add integration**, search for **Odecet.info**, and enter the account.

You can open this repository in HACS with the badge above.

## Setup

The first screen asks for:

| Field | Purpose |
| --- | --- |
| Email | The address used on the odecet.info sign-in page. |
| Password | Stored in the Home Assistant config entry. It is not written to logs. |
| Sign-in URL | The page that contains the login form. The default is `https://odecet.info/signin`. |

The second screen asks for:

| Field | Purpose |
| --- | --- |
| Meters | Cold water, hot water, and heat. Only types found on the account can be selected. Readings for types you leave out are ignored. |
| How to read the history | **Auto (CSV, then table)** tries the CSV export first, then the history table. **CSV export** or **History table** forces one method. |
| Sync from | Readings before this date are ignored. Leave it empty to keep the history the site returns. |

The same three fields can be changed later: **Settings → Devices & services → Odecet.info → Configure**.

After setup, the account device shows **Sync now** and **Next manual sync**. Each meter is its own device, named with the medium and the serial in brackets, and a **Reading** sensor.

Water readings labeled `m3` are stored as cubic metres and can be added to the Energy dashboard as water. Heat with an empty unit is stored as `scale units`. It is a running counter, it is not energy, and it is not added to the Energy dashboard. A water row that arrives with no unit still raises a repair. The integration does not invent `kWh` or `GJ`.

## Use

Follow a flat's water registers in Home Assistant and on the Energy dashboard. A repair opens when the daily read keeps failing, or when a water meter arrives without a unit.

Notify when a meter has been unavailable for an hour. Replace the entity id with the sensor from your account.

```yaml
alias: Odecet.info meter unavailable
triggers:
  - trigger: state
    entity_id: sensor.cold_water_s_n_SERIAL_reading
    to: unavailable
    for:
      hours: 1
actions:
  - action: notify.persistent_notification
    data:
      title: odecet.info
      message: A meter has been unavailable for an hour.
```

## Limitations

- The integration is unofficial.
- A change to the site's login or history page can break sync until the integration is updated.
- Heat with an empty unit is stored as `scale units`. It is not energy and it is not added to the Energy dashboard. The integration does not invent `kWh` or `GJ`. A water row with no unit still raises a repair.
- Automatic and manual sync share a limit of one request per minute.
- Readings before **Sync from** are ignored. The site also limits how much history it returns.
- There is no local connection to a meter. The account has to be able to sign in on the website.

## Remove

**Settings → Devices & services → Odecet.info**, open the menu, and choose **Delete**. To drop the download as well, remove the repository in HACS and restart Home Assistant.

## Debug

- **Settings → System → Logs**, filter for `odecet_info`. A failed read is logged once when it starts and once when it recovers. The password is not logged.
- A repair issue is raised when a meter has no recognizable unit, or when daily sync keeps failing.
- **Settings → Devices & services → Odecet.info → Download diagnostics** lists meters, warnings, and the last sync result. It does not include the password or session cookies.
- If the site layout changes, the CSV path is the more stable one. Switch **How to read the history** under **Configure** and sync again.

## Develop

Local checks are described in [docs/testing.md](docs/testing.md). Copy [.env.example](.env.example) to `.env` for discovery and for the local Home Assistant container. Do not commit `.env`.

```bash
uv run pytest
docker compose -f dev/docker-compose.yml up -d --build
uv run python dev/bootstrap_ha.py --local
```

`dev/inspect_account.py` signs in with `.env` and downloads readings without starting Home Assistant. It prints each meter's span. It does not print the password.

```bash
uv run python dev/inspect_account.py login
uv run python dev/inspect_account.py fetch --method auto
uv run python dev/inspect_account.py fetch --method csv --sync-from 2024-01-01 --json /tmp/odecet.json --csv /tmp/odecet.csv
```

`--method` is `auto`, `csv`, or `table`. The JSON and CSV files are for you. Do not commit them.

## License

[MIT](LICENSE). The unofficial-project disclaimer is in [NOTICE](NOTICE). The license file itself stays plain MIT so GitHub and HACS can identify it.
