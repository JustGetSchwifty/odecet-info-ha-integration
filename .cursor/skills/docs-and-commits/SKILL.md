---
name: docs-and-commits
description: Update English docs and their Czech twins, then create local git commits after each logical chunk. Use when finishing a chunk, writing commit messages, or deciding whether a push is allowed.
---

# Docs and commits

## Docs

Keep these files true for the code that is about to be committed:

| File | Update when |
| --- | --- |
| `README.md` and `docs/cs/README.md` | Install, configuration, entities, or debugging steps change |
| `docs/architecture.md` and `docs/cs/architecture.md` | Modules, scheduling, or entity model change |
| `docs/website-contract.md` and `docs/cs/website-contract.md` | Login, export URL, columns, or units change |
| `docs/challenges.md` and `docs/cs/challenges.md` | A non-obvious site or Home Assistant problem is solved |
| `docs/testing.md` and `docs/cs/testing.md` | Commands, tiers, or fixtures change |
| `docs/heat-cost-allocation.md` and `docs/cs/heat-cost-allocation.md` | The heat reading explanation changes |
| `CHANGELOG.md`, `docs/cs/CHANGELOG.md`, `version.json` | A version is cut. See `.cursor/skills/versioning/SKILL.md` |
| `AGENTS.md`, `.cursor/rules/`, `.cursor/skills/` | The working agreement changes |

Write the English page and the Czech twin in the same change. The first line of both links to the other language. A new string in `strings.json` is copied to `translations/en.json` and translated in `translations/cs.json` in that change. Code, identifiers, logs, skills, rules, and commit messages stay English. Do not mention values from `.env` or anything under `.private/`.

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
