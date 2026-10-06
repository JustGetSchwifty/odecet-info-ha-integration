---
name: tier2-ha
description: Run local Home Assistant against the working tree before a push, and a HACS download only after a push or GitHub release. Use when preparing a push, verifying install, or checking live odecet.info data.
---

# Tier 2 Home Assistant

HACS downloads a commit that is already on GitHub. It cannot see unpushed work. Before a push, test the files on disk. After a push or a release, test the HACS download of that published ref.

## Before a push

Copy the working tree into the local Home Assistant config and reload it. This is a local install. It is not a HACS download.

```bash
docker compose -f dev/docker-compose.yml up -d --build
uv run python dev/bootstrap_ha.py --local
```

Done means Home Assistant answers on `http://127.0.0.1:8123`, meter sensors exist, and their states are numeric. Log in as `dev` / `dev`. That password is only for this container.

Config is stored in `dev/ha-config/`, which is gitignored because it contains the odecet.info password.

## After a push or a release

HACS is the check that users can fetch what was published. Once a GitHub Release exists, HACS installs the latest release, not `main`. A bare tag does not count. Download that release tag:

```bash
uv run python dev/bootstrap_ha.py --hacs --version vX.Y.Z
```

While the repository has no release yet, `uv run python dev/bootstrap_ha.py --hacs` downloads the default branch that is already on GitHub.

Do not push merely so this HACS check can see a commit. Push only when the user asks, or when cutting a minor or patch release as described in `.cursor/skills/versioning/SKILL.md`.

```bash
GIT_SSH_COMMAND="ssh -i .private/deploy -o IdentitiesOnly=yes -o StrictHostKeyChecking=accept-new" git push -u origin HEAD
```

Do not print the key. Do not copy it anywhere else.

The container is left running.
