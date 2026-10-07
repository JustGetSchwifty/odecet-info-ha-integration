# Testing

<p align="center">
  <a href="testing.md"><img alt="English" src="https://img.shields.io/badge/English-1f6feb?style=for-the-badge"></a>
  <a href="cs/testing.md"><img alt="Čeština" src="https://img.shields.io/badge/%C4%8Ce%C5%A1tina-6e7681?style=for-the-badge"></a>
</p>

Tier 1 is fast and never contacts odecet.info. Before a push, tier 2 loads the working tree into local Home Assistant. After a push or a GitHub release, a separate command checks that HACS can download that published ref.

## Tier 1

Run this after a larger change, before treating that change as done.

```bash
uv run ruff check custom_components tests
uv run mypy
uv run pytest
```

`mypy` is strict for `custom_components/odecet_info`. `pytest` fails when coverage of that package drops below 95 percent. CI runs both, and it also runs every night and on demand so a new hassfest or HACS rule is caught without a push.

`tests/test_publish.py` checks the tree for the hassfest and HACS failures that do not need GitHub: manifest key order, the recorder dependency, the integration brand icon, and a LICENSE file GitHub can identify as MIT. The same hassfest image CI uses can be run locally:

```bash
docker run --rm -v "$PWD://github/workspace" ghcr.io/home-assistant/hassfest
```

In Actions, `dev/check_github_metadata.py` checks the detected SPDX license and that the repository has a topic HACS counts. Generic topics such as `home-assistant` and `hacs` do not count. This repository uses `water`, `energy`, and `metering`.

The suite covers:

- A valid sign-in (`True`) and the honeypot, antiforgery token, bad password, timeout, HTTP 429, and HTTP 503
- HTML and CSV that describe the same meters, including decimal commas, duplicate rows, missing columns, a login page returned as CSV, unknown types, missing units, and a decreasing register
- The config flow, including an account that is already set up and an account with no meters
- Sensors, the one-minute cooldown, statistic rows, and the repair raised when a unit is missing

Fixtures in `tests/fixtures/` are synthetic. Live captures stay in gitignored `dev/capture/`.

`dev/inspect_account.py` is the live counterpart. It uses `.env`, prints the span of each meter, and can write JSON or CSV. Tests for it use the scripted session and never call the site.

## Tier 2 before a push

HACS downloads GitHub. A commit that is only on this machine is not in that download, so the pre-push check copies `custom_components/odecet_info` into the container config and restarts Home Assistant. That copy is a local install, not a HACS install.

```bash
docker compose -f dev/docker-compose.yml up -d --build
uv run python dev/bootstrap_ha.py --local
```

## HACS after a push or release

Run this only after the commit or release is already on GitHub. It proves HACS can fetch what users get. After the first GitHub Release, HACS installs the latest release instead of `main`, and a tag without a release does not count.

```bash
uv run python dev/bootstrap_ha.py --hacs --version vX.Y.Z
```

HACS normally stops to ask for a GitHub device login. The bootstrap does not have a GitHub session, so it stores the HACS entry without a token and downloads this public repository anyway. You can connect GitHub later from the HACS panel if the unauthenticated API is rate limited.

The container keeps its config in gitignored `dev/ha-config/`. That directory contains the odecet.info password after bootstrap, so it must not be committed.

Local Home Assistant:

| | |
| --- | --- |
| URL | http://127.0.0.1:8123 |
| Username | `dev` |
| Password | `dev` |

Those credentials exist only for this container. They are not the odecet.info account.

Bootstrap is finished when meter sensors exist and their states are numbers. The container is left running.
