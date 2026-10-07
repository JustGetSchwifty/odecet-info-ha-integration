# Agent guide

This repository is an unofficial Home Assistant integration for odecet.info.
Read this file at the start of every task, then follow the Cursor rules and skills it points at.

## Language

Code, identifiers, comments, log messages, skills, rules, and commit messages are English.

User-facing pages exist in English and Czech. In the same commit, update both:

- `README.md` and `docs/cs/README.md`
- `CHANGELOG.md` and `docs/cs/CHANGELOG.md`
- `docs/heat-cost-allocation.md` and `docs/cs/heat-cost-allocation.md`

`strings.json` and `translations/en.json` stay the same English text. `translations/cs.json` is the Czech UI and changes with them. Developer docs (`architecture`, `testing`, `website-contract`, `challenges`) stay English. Do not skip the Czech twin.

## Secrets

`.env` and `.private/` are out of bounds for git, documentation, skills, and commit messages.

- `.env` holds the live sign-in URL, username, and password for local discovery and the tier-2 Home Assistant instance.
- `.private/deploy` is an SSH deploy key. Use it only as `GIT_SSH_COMMAND="ssh -i .private/deploy -o IdentitiesOnly=yes"` when a push is explicitly allowed.
- `dev/capture/` and `dev/ha-config/` contain account data. They are gitignored. Tests use synthetic fixtures.

Never log passwords, antiforgery tokens, or session cookies.

## How to work

1. Keep changes small and match the patterns already in the tree. Extend a parser, client, or entity base instead of copying it.
2. Update the docs and agent instructions in the same change when behavior, the website contract, or the test process changes.
3. Run tier-1 tests before calling a chunk done. See `.cursor/skills/tier1-tests/SKILL.md`.
4. Before any git push, run the local Home Assistant check (`bootstrap_ha.py --local`). It copies the working tree. It does not download HACS. See `.cursor/skills/tier2-ha/SKILL.md`.
5. Commit each logical chunk locally with a short English message. Do not push unless the user asks. A minor or patch version cut also publishes a GitHub release; see `.cursor/skills/versioning/SKILL.md`. After that release is on GitHub, run `bootstrap_ha.py --hacs --version vX.Y.Z`.

## Where the rules live

- `.cursor/rules/project.mdc` — language, secrets, docs, commits
- `.cursor/rules/python.mdc` — Python design
- `.cursor/rules/home-assistant.mdc` — integration patterns and the quality-scale file
- `.cursor/skills/site-client/SKILL.md` — login, parsing, fixtures
- `.cursor/skills/versioning/SKILL.md` — semver, changelog, GitHub releases
- `docs/` — architecture, website contract, challenges, testing
