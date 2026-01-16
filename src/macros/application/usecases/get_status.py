from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from macros.application.container import Container
from macros.infrastructure.runtime.utils.workspace import get_workspace


@dataclass
class CycleInfo:
    """Summary information about a cycle."""
    cycle_id: str
    macro_id: str
    started_at: datetime
    cycle_dir: str
    step_count: int


def get_status(container: Container) -> CycleInfo | None:
    """Return info about the most recent cycle, or None if no cycles exist."""
    cycles_dir = get_workspace() / ".macrocycle" / "cycles"

    if not cycles_dir.exists():
        return None

    # Get all cycle directories sorted by name (which includes timestamp)
    cycle_dirs = sorted(cycles_dir.iterdir(), reverse=True)

    if not cycle_dirs:
        return None

    latest = cycle_dirs[0]
    return _parse_cycle_dir(latest)


def _parse_cycle_dir(cycle_path: Path) -> CycleInfo:
    """Parse a cycle directory into CycleInfo."""
    # Format: 2025-01-15_14-32-01_fix_abc123
    name = cycle_path.name
    parts = name.split("_")

    # Parse timestamp from first two parts: 2025-01-15_14-32-01
    timestamp_str = f"{parts[0]}_{parts[1]}"
    started_at = datetime.strptime(timestamp_str, "%Y-%m-%d_%H-%M-%S")

    # Macro ID is the third part
    macro_id = parts[2] if len(parts) > 2 else "unknown"

    # Count completed steps
    steps_dir = cycle_path / "steps"
    step_count = len(list(steps_dir.glob("*.md"))) if steps_dir.exists() else 0

    return CycleInfo(
        cycle_id=name,
        macro_id=macro_id,
        started_at=started_at,
        cycle_dir=str(cycle_path),
        step_count=step_count,
    )
