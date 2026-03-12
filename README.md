# macrocycle

> Closed-loop AI agent workflows.

Phase-based execution with validation feedback -- each phase is a control loop where the agent iterates until tests pass, linters are clean, or whatever your definition of done is.

## Why?

AI agents are powerful but undisciplined. They rush to implement, skip analysis, and produce brittle code. Macrocycle fixes this by forcing your agent through structured phases with **automated validation feedback loops**.

The control loop is the product. Integrations (Sentry, GitHub, etc.) are left to the IDE or tools like Claude Code.

## Installation

```bash
pipx install macrocycle
```

## Quick Start

```bash
macrocycle init                               # Initialize .macrocycle/
macrocycle run fix "ValueError in process_request"  # Run workflow
macrocycle run fix "..." --until analyze      # Stop after a phase
macrocycle list                               # List workflows
macrocycle status                             # Latest run info
```

## How It Works

Each **workflow** is a graph of **phases**. Each phase is a closed-loop control system:

```
Phase = Control Loop
  ┌──────────┐    ┌──────────┐    ┌──────────┐
  │ Setpoint │───>│Controller│───>│ Actuator  │
  │(success  │    │(Phase    │    │(AI Agent) │
  │ criteria)│    │Executor) │    └─────┬─────┘
  └──────────┘    └────┬─────┘          │
                       │           ┌────▼─────┐
                  ┌────▼─────┐     │  Plant   │
                  │  Error   │<────│(Codebase)│
                  │  Signal  │     └────┬─────┘
                  └──────────┘     ┌────▼─────┐
                       ^           │  Sensor  │
                       └───────────│(pytest,  │
                                   │ ruff...) │
                                   └──────────┘
```

1. **Execute** steps (LLM prompts, shell commands)
2. **Validate** via a shell command (the sensor)
3. If validation fails, **feed the error back** into the next iteration
4. Repeat until convergence or iteration budget exhausted
5. Route to next phase

## Workflow Definition

Workflows live in `.macrocycle/workflows/` as JSON:

```json
{
  "id": "fix",
  "name": "Fix Issue",
  "agent": {"engine": "cursor"},
  "phases": [
    {
      "id": "analyze",
      "steps": [{"id": "impact", "type": "llm", "prompt": "Analyze: {{INPUT}}"}],
      "on_complete": "implement"
    },
    {
      "id": "implement",
      "steps": [
        {"id": "code", "type": "llm", "prompt": "Implement: {{PHASE_OUTPUT:analyze}}"},
        {"id": "test", "type": "command", "command": "pytest --tb=short"}
      ],
      "validation": {"command": "pytest -q"},
      "max_iterations": 5,
      "context": ["analyze"],
      "on_complete": "review"
    },
    {
      "id": "review",
      "steps": [{"id": "review", "type": "llm", "prompt": "Review changes..."}],
      "validation": {"command": "pytest && ruff check ."},
      "max_iterations": 3,
      "context": ["implement"]
    }
  ]
}
```

**Step types:** `llm` (AI prompt) / `command` (shell command)

**Variables:** `{{INPUT}}` / `{{PHASE_OUTPUT:id}}` / `{{STEP_OUTPUT:id}}` / `{{ITERATION}}` / `{{VALIDATION_OUTPUT}}`

**Agent config cascade:** Workflow -> Phase -> Step (use cheaper models for iteration-heavy phases)

## Artifacts

```
.macrocycle/
  workflows/fix.json
  runs/
    20260312_143052_fix/
      input.txt
      manifest.json        # Checkpoint for crash recovery
      analyze/output.md
      implement/output.md
      review/output.md
```
