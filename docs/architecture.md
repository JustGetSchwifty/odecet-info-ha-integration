# Architecture

<p align="center">
  <a href="architecture.md"><img alt="English" src="https://img.shields.io/badge/English-1f6feb?style=for-the-badge"></a>
  <a href="cs/architecture.md"><img alt="Čeština" src="https://img.shields.io/badge/%C4%8Ce%C5%A1tina-6e7681?style=for-the-badge"></a>
</p>

The integration is one Home Assistant config entry per odecet.info account. Code that talks to the site does not import Home Assistant, so the parser tests run without it.

```text
config flow  -> dedicated session -> OdecetClient.async_fetch
coordinator  -> dedicated session -> OdecetClient.async_fetch -> ReadingSet
sensors      -> latest register, and hourly statistics when the unit is known
button       -> coordinator refresh, blocked for 60 seconds after the last attempt
```

## Modules

| Module | Role |
| --- | --- |
| `client.py` | Sign-in, period form, CSV or HTML fetch |
| `parse.py` | Table and CSV to readings. Bad rows become issues |
| `html_extract.py` | Forms and tables from the server HTML |
| `statistics.py` | Hourly `state` and consumption `sum` |
| `config_flow.py` | Account, then the meter types that were actually found |
| `coordinator.py` | Daily schedule, failure backoff, repair issues |
| `sensor.py` | One register per meter, plus the next-manual-sync timestamp |
| `button.py` | Sync now |

## Session

The client accepts an `aiohttp` session and does not create one. The coordinator creates a session with `async_create_clientsession` while the config entry is being set up, so Home Assistant closes it on unload. Setup and options probes create a session with `auto_cleanup=False` and close it before the step returns. Login cookies never go on the shared Home Assistant session.

## Quality scale

`quality_scale.yaml` records every published rule as `done` or `exempt`. The manifest says `platinum` because that file is complete. Home Assistant does not review custom integrations, so the mark is this repository's assessment against the published rules.

## Scheduling

There is no short polling interval. A successful sync schedules 04:00 local time plus up to 30 minutes of jitter. A failure schedules an exponential backoff that is never shorter than 60 seconds. After five failures a repair is opened and the next attempt is the following daily slot. An authentication failure starts the reauth flow instead.

The manual button and the schedule share `last_attempt`. While that timestamp is less than a minute old, the button is unavailable and `sensor.<account>_next_manual_sync` is in the future. Home Assistant renders that timestamp as a relative countdown.

## Entities

The account device is created before any meter device. Each meter is its own device, linked with `via_device`, because a meter that points at a missing device is rejected. The meter device name is translated: `Heat [S/N {serial}]` in English and `Teplo [číslo {serial}]` in Czech. The account device keeps the email as its name.

Water with `m³` or `L` is `device_class: water` and `state_class: total_increasing`. Heat with an empty unit is `scale units` and `total_increasing`, with no energy device class, so it stays off the Energy dashboard. Its hourly history is still imported. Heat that arrives with `kWh` or `GJ` is `device_class: energy`. A water meter with no unit stays a raw number and raises a repair.

Statistics use `async_import_statistics` with `source: recorder` and the sensor's entity id. That is the same series the Energy dashboard reads. A second external statistic is not created.

## Options

Credentials and the sign-in URL are entry data. Enabled mediums, fetch method, and the sync-from date are options. Changing options reloads the entry. Mediums that were not in the latest sign-in are omitted from the selector and named in the form description. Home Assistant cannot grey out one option inside a selector.
