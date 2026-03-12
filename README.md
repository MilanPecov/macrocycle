# macrocycle

> Your StarCraft macro loop for code.

Ritualized AI agent workflows — multi-pass prompt pipelines that turn any AI coding agent into a disciplined control loop.

## Why?

AI agents are powerful but undisciplined. They rush to implement, skip analysis, and produce brittle code. Macrocycle fixes this by forcing your agent through a structured loop — analysis, planning, rejection, implementation, review — before it ships anything.

The control loop is the product. Integrations (Sentry, GitHub, etc.) are left to the IDE or tools like Claude Code and OpenClaw.

## How It Works

Define a **macro** — a sequence of LLM prompts and human gates — and run it against any input. Each pass builds on the last, producing auditable artifacts at every step.

```
Input → [impact → plan → reject → approve → implement → review → simplify → PR] → Output
          LLM     LLM     LLM      GATE       LLM        LLM      LLM      LLM
```

**LLM steps** send prompts to your agent. **Gate steps** pause for human approval. Previous step outputs flow forward as context, so each step builds on the last.

## Quick Start

```bash
pip install macrocycle
macrocycle init
macrocycle run fix "TypeError: cannot unpack non-iterable NoneType object in auth.py:42"
```

## Commands

```bash
macrocycle init                        # Scaffold .macrocycle/ with default macros
macrocycle list                        # List available macros
macrocycle run <macro> "<input>"       # Execute a macro
macrocycle run <macro> -i file.txt     # Input from file
macrocycle run <macro> --dry-run       # Preview prompts without running
macrocycle run <macro> --yes           # Auto-approve all gates
macrocycle run <macro> --until <step>  # Stop after a specific step
macrocycle status                      # Show last cycle result
echo "..." | macrocycle run fix        # Pipe from stdin
```

## The Default `fix` Macro

Eight steps, designed to prevent the most common AI coding failures:

| Step | Type | Purpose |
|------|------|---------|
| impact | LLM | Deep analysis of the problem |
| plan | LLM | Concrete, scoped fix plan |
| reject | LLM | Adversarial review — force refinement |
| approve | Gate | Human checkpoint before implementation |
| implement | LLM | Write the actual code |
| review | LLM | Self-review for bugs and edge cases |
| simplify | LLM | Clean up, follow conventions |
| PR | LLM | Ship with a clear description |

## Custom Macros

Create `.macrocycle/macros/your-macro.json`:

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
**Variables:** `{{INPUT}}` (original input) · `{{STEP_OUTPUT:step_id}}` (output from a previous step)

## Artifacts

Every cycle is saved to disk. Nothing is lost, everything is reviewable.

```
.macrocycle/
  macros/fix.json
  cycles/
    2026-03-12_fix_abc123/
      input.txt
      steps/01-impact.md
      steps/02-plan.md
      ...
```

## Development

```bash
git clone https://github.com/MilanPecov/macrocycle.git
cd macrocycle
pip install -e ".[dev]"
pytest
```
