from datetime import datetime
from pathlib import Path

from macros.application.dto import CycleInfo


class CycleDirParser:
    """Parses cycle directory structure into CycleInfo."""

    @staticmethod
    def parse(cycle_path: Path) -> CycleInfo:
        """Parse a cycle directory into CycleInfo.
        
        Directory format: 2025-01-15_14-32-01_fix_abc123
        """
        name = cycle_path.name
        parts = name.split("_")

        timestamp_str = f"{parts[0]}_{parts[1]}"
        started_at = datetime.strptime(timestamp_str, "%Y-%m-%d_%H-%M-%S")
        macro_id = parts[2] if len(parts) > 2 else "unknown"

        steps_dir = cycle_path / "steps"
        step_count = len(list(steps_dir.glob("*.md"))) if steps_dir.exists() else 0

        return CycleInfo(
            cycle_id=name,
            macro_id=macro_id,
            started_at=started_at,
            cycle_dir=str(cycle_path),
            step_count=step_count,
        )
