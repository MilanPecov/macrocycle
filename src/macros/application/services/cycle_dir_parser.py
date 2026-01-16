from datetime import datetime
from pathlib import Path

from macros.domain.model import CycleInfo


class CycleDirParser:
    """Parses cycle directory structure into CycleInfo."""

    @staticmethod
    def parse(cycle_path: str) -> CycleInfo:
        """Parse a cycle directory path into CycleInfo.
        
        Directory format: 2025-01-15_14-32-01_fix_abc123
        """
        path = Path(cycle_path)
        name = path.name
        parts = name.split("_")

        timestamp_str = f"{parts[0]}_{parts[1]}"
        started_at = datetime.strptime(timestamp_str, "%Y-%m-%d_%H-%M-%S")
        macro_id = parts[2] if len(parts) > 2 else "unknown"

        steps_dir = path / "steps"
        step_count = len(list(steps_dir.glob("*.md"))) if steps_dir.exists() else 0

        return CycleInfo(
            cycle_id=name,
            macro_id=macro_id,
            started_at=started_at,
            cycle_dir=cycle_path,
            step_count=step_count,
        )
