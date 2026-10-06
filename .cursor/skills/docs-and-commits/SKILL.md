---
name: docs-and-commits
description: Update English docs and create local git commits after each logical chunk. Use when finishing a chunk, writing commit messages, or deciding whether a push is allowed.
---

# Docs and commits

## Docs

Keep these files true for the code that is about to be committed:

| File | Update when |
| --- | --- |
| `README.md` | Install, configuration, entities, or debugging steps change |
| `docs/architecture.md` | Modules, scheduling, or entity model change |
| `docs/website-contract.md` | Login, export URL, columns, or units change |
| `docs/challenges.md` | A non-obvious site or Home Assistant problem is solved |
| `docs/testing.md` | Commands, tiers, or fixtures change |
| `CHANGELOG.md`, `version.json` | A version is cut. See `.cursor/skills/versioning/SKILL.md` |
| `AGENTS.md`, `.cursor/rules/`, `.cursor/skills/` | The working agreement changes |

Write them in English. Do not mention values from `.env` or anything under `.private/`.

## Commits

Create one commit per logical chunk, without being asked again. The policy is already approved for this repository.

```bash
git add <files that belong to the chunk>
git commit -m "$(cat <<'EOF'
Subject in the imperative.

Why this change exists, if the subject does not say it.
EOF
)"
```

Before staging, run `git status` and confirm `.env`, `.private/`, `dev/capture/`, and `dev/ha-config/` are absent.

## Push

Do not push after a commit.

Push only when:

- the user explicitly asks, or
- a minor or patch version cut is being published, including its annotated tag and GitHub Release.

Do not push so that HACS can see an unpublished commit. Pre-push testing copies the local tree. See `.cursor/skills/tier2-ha/SKILL.md`.

Use the deploy key and then stop:

```bash
GIT_SSH_COMMAND="ssh -i .private/deploy -o IdentitiesOnly=yes -o StrictHostKeyChecking=accept-new" git push -u origin HEAD
```
