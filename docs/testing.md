# Testing

Tier 1 is fast and never contacts odecet.info. Tier 2 boots Home Assistant and installs this repository through HACS.

## Tier 1

Run this after a larger change, before treating that change as done.

```bash
uv run ruff check custom_components tests
uv run pytest
```

The suite covers:

- A valid sign-in (`True`) and the honeypot, antiforgery token, bad password, timeout, HTTP 429, and HTTP 503
- HTML and CSV that describe the same meters, including decimal commas, duplicate rows, missing columns, a login page returned as CSV, unknown types, missing units, and a decreasing register
- The config flow, including an account that is already set up and an account with no meters
- Sensors, the one-minute cooldown, statistic rows, and the repair raised when a unit is missing

Fixtures in `tests/fixtures/` are synthetic. Live captures stay in gitignored `dev/capture/`.

## Tier 2

Run this before every git push. It is the check that the integration actually installs from GitHub.

```bash
docker compose -f dev/docker-compose.yml up -d --build
uv run python dev/bootstrap_ha.py
```

HACS can only download a public GitHub repository. If the commits are not on the remote yet, push with the deploy key first, then run the bootstrap again. The key stays in `.private/deploy` and is not copied anywhere else.

HACS normally stops to ask for a GitHub device login. The bootstrap does not have a GitHub session, so it stores the HACS entry without a token and downloads this public repository anyway. You can connect GitHub later from the HACS panel if the unauthenticated API is rate limited.

```bash
GIT_SSH_COMMAND="ssh -i .private/deploy -o IdentitiesOnly=yes -o StrictHostKeyChecking=accept-new" git push -u origin HEAD
```

The container keeps its config in gitignored `dev/ha-config/`. That directory contains the odecet.info password after bootstrap, so it must not be committed.

Local Home Assistant:

| | |
| --- | --- |
| URL | http://127.0.0.1:8123 |
| Username | `dev` |
| Password | `dev` |

Those credentials exist only for this container. They are not the odecet.info account.

Bootstrap is finished when meter sensors exist and their states are numbers. The container is left running.
