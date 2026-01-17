# AGENT.md

Architecture reference for AI agents and contributors.

## Design Philosophy

**Functional core, imperative shell.** Pure business logic lives at the center; IO-bound code lives at the edges. This separation yields testability—domain logic can be verified without mocking, infrastructure can be swapped without touching business rules.

**Dependencies flow inward.** Outer layers know about inner layers, never the reverse. The domain defines what it needs through ports (interfaces); infrastructure satisfies those contracts. This inverts the typical dependency direction—the domain drives, infrastructure follows.

**Make implicit concepts explicit.** When a concept appears repeatedly in conversation or code, give it a name and a home. `Cycle` emerged because "a running macro execution" kept appearing. `Step` became a discriminated union because "something that can be an LLM call or a gate" deserved first-class representation.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  CLI              Thin orchestration—parse, delegate, format    │
├─────────────────────────────────────────────────────────────────┤
│  APPLICATION      usecases/ (commands)  presenters/ (output)    │
│                   services/ (app logic) container.py (wiring)   │
├─────────────────────────────────────────────────────────────────┤
│  DOMAIN (pure)    model/ (entities)     ports/ (interfaces)     │
│                   services/ (logic)     exceptions.py           │
├─────────────────────────────────────────────────────────────────┤
│  INFRASTRUCTURE   persistence/ (files)  runtime/ (agents, IO)   │
└─────────────────────────────────────────────────────────────────┘
```

## Domain Layer

The functional core. No IO, no framework dependencies, no awareness of how it's persisted or presented.

**Aggregates** are consistency boundaries—clusters of objects treated as a unit for data changes:

- `Cycle` — The aggregate root for execution. A cycle tracks its status, timing, and accumulated step results. External code references cycles by ID; only the `CycleOrchestrator` mutates cycle state.
- `Macro` — The aggregate root for workflow definitions. Immutable once loaded. Contains an ordered sequence of `Step` objects that define the ritual.

**Value Objects** are immutable and compared by value:
- `Step` — Discriminated union: `LlmStep` (AI execution) | `GateStep` (human approval)
- `StepRun` — Immutable record of executing a single step

**Ports** define the contracts infrastructure must fulfill. They speak the language of the domain—never leaking infrastructure concerns upward:
- `AgentPort` — Execute a prompt, return exit code and output
- `CycleStorePort` — Create directories, write artifacts, find latest cycle
- `ConsolePort` — User interaction: info, warn, confirm
- `MacroRegistryPort` — List and load macro definitions

**Services** encapsulate domain logic that doesn't belong to a single entity:
- `CycleOrchestrator` — The heart of the system. Executes macros step-by-step, handling gates and failures.
- `PromptBuilder` — Assembles prompts with context from previous steps
- `TemplateRenderer` — Resolves `{{VARIABLE}}` placeholders
- `MacroValidator` — Enforces macro invariants

## Application Layer

Orchestrates domain and infrastructure to fulfill user intent. Use cases are deliberately thin—they wire dependencies and delegate. Business logic belongs in domain services; presentation logic belongs in presenters.

| Folder | Purpose |
|--------|---------|
| `usecases/` | `run_macro`, `init_repo`, `get_status`, `preview_macro`, `list_macros` |
| `services/` | `PreviewBuilder` (builds preview DTOs), `CycleDirParser` (parses paths to info) |
| `presenters/` | Formatting for CLI output—keeps presentation concerns out of domain |
| `container.py` | Wires infrastructure adapters. Domain services instantiate their own dependencies. |

## Infrastructure Layer

The imperative shell. All file access, subprocess calls, and user IO live here.

| Folder | Adapters |
|--------|----------|
| `persistence/` | `FileMacroStore`, `FileCycleStore`, `MacroJsonMapper` |
| `runtime/` | `CursorAgentAdapter`, `StdConsoleAdapter` |

Adapters implement ports. The domain says "I need to persist artifacts"—infrastructure decides that means "write to `.macrocycle/cycles/`".

## Data Flow

`macrocycle run fix "error"` →  
CLI creates Container (wires infrastructure) → `run_macro` use case loads `Macro` via port → creates `CycleOrchestrator` with injected ports → orchestrator runs the cycle: creates directory, iterates steps, builds prompts, calls agent, handles gates → returns `Cycle` → CLI formats and displays.

## Testing Strategy

The architecture enables focused testing at each layer:

- **Domain:** Unit tests on pure functions. Pass data in, assert data out. No mocks needed—these are calculations.
- **Application:** Mock the ports to test orchestration logic in isolation.
- **Infrastructure:** Integration tests with real files in temp directories.

## Naming Conventions

- `*_port.py` — Protocol interface (what the domain needs)
- `*_store.py` — Persistence adapter (how infrastructure provides it)
- `*_mapper.py` — Data transformation between formats
- `*_builder.py` — Complex object construction

## Extending the System

| Task | Approach |
|------|----------|
| New step type | Add variant to `Step` union in `domain/model/macro.py`, handle in `CycleOrchestrator` |
| New persistence | Define port in `domain/ports/`, implement adapter in `infrastructure/persistence/` |
| New agent | Implement `AgentPort`, register in `Container.AGENT_REGISTRY` |
| New command | Add use case in `application/usecases/`, wire in `cli.py` |

## Guiding Principles

1. **Ports return primitives or domain types**—never infrastructure types. If you're returning a `Path`, something is wrong.
2. **Use cases delegate; domain services compute.** A use case that contains business logic has misplaced responsibilities.
3. **Container wires infrastructure only.** Domain services create their collaborators internally or receive them through ports.
4. **CLI is presentation.** Parse input, call use case, format output. No decisions about business rules.
5. **Explicit over implicit.** Clear dependencies, no magic, no action at a distance.
