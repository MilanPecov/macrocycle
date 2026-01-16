# Development

## Development Setup

```bash
git clone https://github.com/MilanPecov/macrocycle.git
cd macrocycle

# Using uv (recommended)
uv venv && source .venv/bin/activate
uv pip install -e .[dev]

# Or using standard venv
python -m venv .venv && source .venv/bin/activate
pip install -e .[dev]
```

## Running Tests

```bash
pytest
```

## Releasing

We use [Commitizen](https://commitizen-tools.github.io/commitizen/) for versioning. Write commits using conventional format:

```bash
git commit -m "feat: add new macro type"    # → minor bump
git commit -m "fix: resolve edge case"      # → patch bump
git commit -m "feat!: breaking change"      # → major bump
```

Then release:

```bash
make release            # Auto-bump based on commits
make release-patch      # 0.1.0 → 0.1.1
make release-minor      # 0.1.0 → 0.2.0
make release-major      # 0.1.0 → 1.0.0
```

Pushing a tag triggers CI → tests → PyPI publish → GitHub release.

## Project Structure

```
src/macros/
├── cli.py                 # Typer CLI entry point
├── application/           # Use cases and dependency container
├── domain/                # Core models, ports, services
└── infrastructure/        # Adapters (file storage, console, agent)
```
