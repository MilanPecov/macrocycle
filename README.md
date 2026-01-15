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

## 🔁 Run at Scale

Loop through problems and let agents work in parallel:

```bash
# Fix all Sentry errors from today
for error in $(sentry-cli issues list --status unresolved); do
  git checkout -b fix/$error
  macrocycle run fix "$(sentry-cli issues get $error)" &
done
```

Each agent runs the full ritual: impact → plan → review → implement → PR.

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

```bash
git clone https://github.com/MilanPecov/macrocycle.git
cd macrocycle

# Using uv (recommended)
uv venv && source .venv/bin/activate
uv pip install -e .[test]

# Or using standard venv
python -m venv .venv && source .venv/bin/activate
pip install -e .[test]
```

## 🧪 Test

```bash
pytest                  # Run all tests
```

## License

MIT
