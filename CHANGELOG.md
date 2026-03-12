# Changelog

All notable changes to this project will be documented in this file.

## v0.4.0 (2026-03-12)

### Feat

- **BREAKING**: replace macro/cycle model with closed-loop workflow engine
- phase-based execution with validation feedback loops
- AgentConfig cascade (Workflow -> Phase -> Step) for multi-model support
- CommandPort for shell-based validation sensors
- checkpoint manifests for crash recovery

### Removed

- Pydantic, Jinja2, Textual dependencies
- GateStep (fully autonomous execution)
- TUI, work item integrations, batch orchestrator

## v0.3.0 (2026-03-12)

### Refactor

- strip integrations layer, focus on core control loop

## v0.2.0 (2026-01-21)

### Feat

- add more e2e tests
- add AGENT.md

### Refactor

- **tests**: consolidate helpers and improve GIVEN/WHEN/THEN structure
- architecture cleanup
- strip integrations layer, focus on control loop

## v0.1.3 (2026-01-16)

### Fix

- default prompt improvement
- architecture cleanup -part 2
- architecture cleanup

### Refactor

- DDD cleanup - simplify layers, remove redundancies

## v0.1.2 (2026-01-15)

### Feat

- improve default workflow prompt
- improve dry-run mode
- add development docs
- add --dry-run and --version
- add --dry-run and --version

### Fix

- update readme
- update readme
- tests

## v0.1.1 (2026-01-15)

### Fix

- use timezone.utc for Python 3.10 compatibility

## v0.1.0 (2025-01-15)

### Features

- Initial release
- `macrocycle init` - Initialize .macrocycle folder
- `macrocycle list` - List available macros  
- `macrocycle run` - Execute macro workflows
- Built-in `fix` macro for error resolution workflows
