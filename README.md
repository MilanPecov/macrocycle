# macrocycle

> Your StarCraft macro loop for code.

Ritualized AI agent workflows - multi-pass prompt pipelines for Cursor and beyond.

## ⚡ Why Macros?

- **Burn tokens, not time.** Let AI iterate through analysis, planning, and implementation while you context-switch.
- **Scale horizontally.** Run 10 agents on 10 Sentry errors. Review the PRs over lunch.
- **Artifacts you can audit.** Every cycle saves outputs to disk. Review before merging.

## 📦 Installation

```bash
pipx install macrocycle
```

Or: `pip install macrocycle` / `uv tool install macrocycle`

## 🚀 Quick Start

```bash
cd your-project
macrocycle init

git checkout -b fix/your-issue
macrocycle run fix "Paste your error context here"
```

## 🔁 Orchestration

Macrocycle is composable — pipe in data from any source, run in parallel, integrate with your toolchain.

**Example: Batch-fix [Sentry](https://sentry.io) errors**

[Sentry](https://sentry.io) is an error monitoring platform. This script pulls unresolved issues from the last 24h and spawns parallel agents to fix each one:

```bash
# Fix all new unresolved issues from the last 24h (with latest event)
set -euo pipefail
: "${SENTRY_AUTH_TOKEN:?}" "${SENTRY_ORG:?}" "${SENTRY_PROJECT:?}"
SENTRY_URL="${SENTRY_URL:-https://sentry.io}"
QUERY='is:unresolved age:-24h'

sentry-cli issues list -o "$SENTRY_ORG" -p "$SENTRY_PROJECT" --query "$QUERY" \
| awk 'NR>3 && $1 ~ /^[0-9]+$/ {print $1}' \
| while read -r issue_id; do
    [ -n "$issue_id" ] || continue
    git checkout -b "fix/sentry-$issue_id"
    macrocycle run fix "$(
      curl -sS -H "Authorization: Bearer $SENTRY_AUTH_TOKEN" \
        "$SENTRY_URL/api/0/organizations/$SENTRY_ORG/issues/$issue_id/"
      echo
      curl -sS -H "Authorization: Bearer $SENTRY_AUTH_TOKEN" \
        "$SENTRY_URL/api/0/organizations/$SENTRY_ORG/issues/$issue_id/events/?full=true&per_page=1"
    )" &
  done

wait
```

Each agent runs the full ritual: impact → plan → reject → approve → implement → review → simplify → PR.

The same pattern works with any issue tracker, log aggregator, or CI pipeline.

## 🛠 CLI Commands

```bash
macrocycle init                      # Initialize .macrocycle folder
macrocycle list                      # List available macros
macrocycle run <macro> <input>       # Run a macro
macrocycle run fix "..." --yes       # Skip gate approvals
macrocycle run fix "..." --until impact  # Stop after specific step
```

## 📁 Artifacts

```
.macrocycle/
  macros/fix.json           # Workflow definitions
  cycles/                   # Execution history
    2026-01-15_fix_abc123/
      input.txt
      steps/01-impact.md
      steps/02-plan.md
      ...
```

## 🧑‍💻 Development

See [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) for setup, testing, and releases.