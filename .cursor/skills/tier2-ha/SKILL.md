---
name: tier2-ha
description: Run the local Docker Home Assistant with HACS and this integration before any git push. Use when preparing a push, verifying install, or checking live odecet.info data in Home Assistant.
---

# Tier 2 Home Assistant

Tier 2 boots a real Home Assistant container, installs this integration through HACS from GitHub, and configures it with the local `.env` account.

## When to run

Run tier 2 before every git push. Also run it when the user asks to see the integration in a local Home Assistant.

HACS can only download a public GitHub repository. If the branch is not on the remote yet, push with the deploy key first, then install. Further pushes are only for fixes that tier 2 needs. Stop pushing after the install works unless the user asks.

```bash
GIT_SSH_COMMAND="ssh -i .private/deploy -o IdentitiesOnly=yes" git push -u origin HEAD
```

Do not print the key. Do not copy it anywhere else.

## How to run

From the repository root:

```bash
docker compose -f dev/docker-compose.yml up -d --build
uv run python dev/bootstrap_ha.py
```

The bootstrap script finishes onboarding, adds `JustGetSchwifty/odecet-info-ha-integration` with the HACS websocket API, downloads it, restarts Home Assistant, and creates the config entry from `.env`.

Config is stored in `dev/ha-config/`, which is gitignored because it contains the account password.

## Done means

- Home Assistant answers on `http://127.0.0.1:8123`
- HACS lists the repository as downloaded
- Meter sensors exist and their states are numeric
- The container is left running

If HACS reports that the repository structure is invalid, fix the repo, commit, push, and run bootstrap again.
