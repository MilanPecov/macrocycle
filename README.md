# macrocycle

> Your StarCraft macro loop for code.

Ritualized AI agent workflows — multi-pass prompt pipelines for Cursor and beyond.

## ⚡ Why Macros?

- **Burn tokens, not time.** Let AI iterate through analysis, planning, and implementation while you context-switch.
- **Scale horizontally.** Spawn parallel agents — 10 errors in, 10 PRs out.
- **Artifacts you can audit.** Every cycle saves outputs to disk. Review before merging.

## 📦 Installation

```bash
pipx install macrocycle
```

Or: `pip install macrocycle` / `uv tool install macrocycle`

---

## Two Ways to Use

### 🖥️ Interactive Mode (TUI)

The terminal UI guides you through batch processing without writing scripts:

```bash
macrocycle tui
```

**Flow:** Select source → Pick issues → Choose workflow → Watch parallel execution → Review results

Ideal for daily triage — connect to Sentry, GitHub, or other integrations and process multiple issues in one session.

### ⌨️ CLI Mode

Direct commands for scripting, CI/CD, and automation:

```bash
macrocycle init                        # Initialize .macrocycle folder
macrocycle run fix "your error"        # Run a macro with input
macrocycle run fix "..." --yes         # Auto-approve all gates
macrocycle run fix "..." --dry-run     # Preview prompts without executing

# Work item integrations
macrocycle work sources                # List available sources
macrocycle work list -s sentry         # Fetch issues from a source
macrocycle work fix <id> -s sentry     # Fix a specific work item
```

Pipe data from any source, parallelize with shell, integrate into your toolchain.

---

## 🔄 The Ritual

The default `fix` macro runs your agent through a structured loop:

```
🔍 impact    → Analyze the problem deeply
📋 plan      → Create a concrete fix plan  
❌ reject    → Force refinement (no hand-waving!)
✅ approve   → Human gate: review & approve
🔨 implement → Execute the plan, write code
🔬 review    → Self-review for bugs & edge cases
✨ simplify  → Clean up, follow conventions
🚀 PR        → Ship it with a clear description
```

## ✏️ Custom Macros

Create workflows in `.macrocycle/macros/`:

```json
{
  "macro_id": "review",
  "name": "Code Review",
  "engine": "cursor",
  "include_previous_outputs": true,
  "steps": [
    { "id": "analyze", "type": "llm", "prompt": "Analyze this code:\n\n{{INPUT}}" },
    { "id": "confirm", "type": "gate", "message": "Apply suggested fixes?" },
    { "id": "fix", "type": "llm", "prompt": "Apply the fixes identified above." }
  ]
}
```

**Step types:** `llm` (agent prompt) · `gate` (human approval)  
**Variables:** `{{INPUT}}` · `{{STEP_OUTPUT:step_id}}`

## 📁 Artifacts

```
.macrocycle/
  macros/fix.json              # Workflow definitions
  cycles/
    2026-01-15_fix_abc123/
      input.txt                # Original input
      steps/01-impact.md       # Each step's output
      steps/02-plan.md
      ...
```

## 🧑‍💻 Development

See [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md).
