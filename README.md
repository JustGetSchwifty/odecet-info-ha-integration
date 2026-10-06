# Odecet.info for Home Assistant

[![CI](https://github.com/JustGetSchwifty/odecet-info-ha-integration/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/JustGetSchwifty/odecet-info-ha-integration/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/JustGetSchwifty/odecet-info-ha-integration?display_name=tag)](https://github.com/JustGetSchwifty/odecet-info-ha-integration/releases)
[![HACS](https://img.shields.io/badge/HACS-Custom-41BDF5)](https://github.com/hacs/integration)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Home Assistant](https://img.shields.io/badge/Home%20Assistant-2025.11%2B-blue)](https://www.home-assistant.io/)

Unofficial Home Assistant integration that reads hot water, cold water, and heat meter history from [odecet.info](https://odecet.info) and exposes one meter sensor per device.

This project is not affiliated with odecet.info or its operator. The site can change or block access at any time. See [LICENSE](LICENSE) and [NOTICE](NOTICE).

## What it does

- Signs in with your odecet.info account from **Settings → Devices & services → Add integration**.
- Imports the measurement history, either from the CSV export or from the history table. You choose which one to use.
- Creates one device and a **Reading** sensor for each meter. Types that are not on the account are not offered.
- Syncs once a day in the background, at about 04:00 local time, with jitter. A failure retries with backoff and never sooner than one minute. After five failures it opens a repair and waits for the next day.
- Adds a **Sync now** button. Manual and automatic syncs share a limit of one sync per minute. **Next manual sync** shows when the button will be available again.
- Ignores readings older than the start date you set.

## Install

The integration is not in the default HACS catalog.

1. Install [HACS](https://www.hacs.xyz/docs/use/download/download/).
2. In HACS, open the three-dot menu and choose **Custom repositories**.
3. Add `https://github.com/JustGetSchwifty/odecet-info-ha-integration` as an **Integration**.
4. Download **Odecet.info**.
5. Restart Home Assistant.
6. Go to **Settings → Devices & services → Add integration**, search for **Odecet.info**, and enter the account.

## Configure

| Setting | Where | Purpose |
| --- | --- | --- |
| Sign-in URL | Setup | Page that contains the login form. The default is `https://odecet.info/signin`. |
| Username and password | Setup | The account email and password. Stored in the config entry, not in YAML. |
| Meters | Setup | Hot water, cold water, and heat. Only types found on the account can be selected. |
| Fetch method | Options | `Auto` tries CSV export, then the history table. `CSV` or `Table` forces one method. |
| Sync from | Options | Readings before this date are ignored. Empty means the full history that the site returns. |

After setup, the account device shows **Sync now** and **Next manual sync**. Each meter is its own device with a **Reading** sensor.

Water readings labeled `m3` are stored as cubic metres and can be added to the Energy dashboard as water. If the site does not send a unit, which is the case for heat on the current pages, the sensor shows the raw register, a repair explains why, and the value is not written to statistics. The integration does not guess a unit.

## Debug

- **Settings → System → Logs**, filter for `odecet_info`. Failed logins, unrecognized pages, and skipped rows are logged there without the password.
- A repair issue is raised when a meter has no recognizable unit, or when daily sync keeps failing.
- **Settings → Devices & services → Odecet.info → Download diagnostics** lists meters, warnings, and the last sync result. It does not include the password or session cookies.
- If the site layout changes, the CSV path is the more stable one. Switch the fetch method in the integration options and sync again.

## Develop

Local checks are described in [docs/testing.md](docs/testing.md). Copy [.env.example](.env.example) to `.env` for discovery and for the local Home Assistant container. Do not commit `.env`.

```bash
uv run pytest
docker compose -f dev/docker-compose.yml up -d --build
uv run python dev/bootstrap_ha.py --local
```

## License

[MIT](LICENSE). The unofficial-project disclaimer is in [NOTICE](NOTICE). The license file itself stays plain MIT so GitHub and HACS can identify it.
