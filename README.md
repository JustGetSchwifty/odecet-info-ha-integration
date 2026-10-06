# Odecet.info for Home Assistant

Unofficial Home Assistant integration that reads hot water, cold water, and heat meter history from [odecet.info](https://odecet.info) and exposes one meter sensor per device.

This project is not affiliated with odecet.info or its operator. The site can change or block access at any time. See [LICENSE](LICENSE).

## What it does

- Signs in with your odecet.info account from **Settings → Devices & services → Add integration**.
- Imports the measurement history, either from the CSV export or from the history table. You choose which one to use.
- Creates a sensor for each meter it finds. Meters that are not on the account are not offered.
- Syncs once a day in the background, with retry and jitter after a failure.
- Offers a manual sync button. Manual and automatic syncs share a limit of one sync per minute, and Home Assistant shows when the next one is allowed.
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

After setup, the device page shows the meters, a **Sync now** button, and a **Next manual sync** timestamp. The button stays unavailable until a minute has passed since the previous attempt.

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
uv run python dev/bootstrap_ha.py
```

## License

[MIT](LICENSE), with an extra disclaimer: unofficial project, no responsibility for future site changes.
