# Agent guide

This repository is an unofficial Home Assistant integration for odecet.info.
Read this file at the start of every task, then follow the Cursor rules and skills it points at.

## Language

Everything written into the repository is English: code, identifiers, comments, UI strings, logs, documentation, skills, rules, and commit messages.

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
4. Run tier-2 before any git push. See `.cursor/skills/tier2-ha/SKILL.md`.
5. Commit each logical chunk locally with a short English message. Do not push unless the user asks, except when tier-2 HACS install cannot proceed without the public GitHub repository. See `.cursor/skills/docs-and-commits/SKILL.md`.

## Where the rules live

- `.cursor/rules/project.mdc` — language, secrets, docs, commits
- `.cursor/rules/python.mdc` — Python design
- `.cursor/rules/home-assistant.mdc` — integration patterns
- `.cursor/skills/site-client/SKILL.md` — login, parsing, fixtures
- `docs/` — architecture, website contract, challenges, testing
