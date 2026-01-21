# macrocycle

> Your StarCraft macro loop for code.

Ritualized AI agent workflows - multi-pass prompt pipelines for Cursor and beyond.

## ⚡ Why Macros?

- **Burn tokens, not time.** Let AI iterate through analysis, planning, and implementation while you context-switch.
- **Scale horizontally.** Spawn parallel agents — 10 errors in, 10 PRs out.
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

## 🖥️ Interactive TUI

Launch the interactive terminal UI for batch processing:

```bash
macrocycle tui
```

The TUI guides you through:
1. **Select a source** — Connect to Sentry, GitHub, or other integrations
2. **Pick issues** — Multi-select work items to process
3. **Choose workflow** — Select which macro to apply
4. **Watch progress** — Live progress bars for parallel execution
5. **Review results** — Summary of succeeded/failed items

Perfect for processing multiple issues without writing scripts.

## 🔄 The Ritual

The default `fix` macro runs your agent through a structured loop:

```
🔍 impact    Analyze the problem deeply
     ↓
📋 plan      Create a concrete fix plan
     ↓
❌ reject    Force refinement (no hand-waving!)
     ↓
✅ approve   Human gate: review & approve
     ↓
🔨 implement Execute the plan, write code
     ↓
🔬 review    Self-review for bugs & edge cases
     ↓
✨ simplify  Clean up, follow conventions
     ↓
🚀 PR        Ship it with a clear description
```

Use `--dry-run` to preview the prompts before running:
```bash
macrocycle run fix "your error" --dry-run
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

Each agent runs the full ritual autonomously. Batch review the PRs when ready.

Works with any issue tracker, log aggregator, or CI pipeline.

## 🛠 CLI Commands

```bash
macrocycle init                      # Initialize .macrocycle folder
macrocycle list                      # List available macros
macrocycle run <macro> <input>       # Run a macro
macrocycle run fix "..." --yes       # Skip gate approvals
macrocycle run fix "..." --until impact  # Stop after specific step
macrocycle tui                       # Launch interactive TUI
macrocycle work sources              # List available integrations
macrocycle work list -s sentry       # List issues from a source
macrocycle work fix <id> -s sentry   # Fix a specific issue
```

## ✏️ Custom Macros

Create your own workflows in `.macrocycle/macros/`:

```json
{
  "macro_id": "review",
  "name": "Code Review",
  "engine": "cursor",
  "include_previous_outputs": true,
  "steps": [
    {
      "id": "analyze",
      "type": "llm",
      "prompt": "Analyze this code for issues:\n\n{{INPUT}}"
    },
    {
      "id": "confirm",
      "type": "gate",
      "message": "Apply suggested fixes?"
    },
    {
      "id": "fix",
      "type": "llm", 
      "prompt": "Apply the fixes identified above."
    }
  ]
}
```

**Step types:**
- `llm` — Send prompt to agent, save output
- `gate` — Pause for human approval (skip with `--yes`)

**Template variables:**
- `{{INPUT}}` — User's original input
- `{{STEP_OUTPUT:step_id}}` — Output from a previous step

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
