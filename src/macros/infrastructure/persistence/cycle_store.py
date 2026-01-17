from datetime import datetime
from pathlib import Path
import secrets

from macros.domain.model import CycleInfo
from macros.domain.ports.cycle_store_port import CycleStorePort
from macros.infrastructure.runtime.utils.workspace import get_workspace


class FileCycleStore(CycleStorePort):
    """File-based cycle artifact storage.
    
    Cycle directories follow the format: {timestamp}_{macro_id}_{suffix}
    Example: 2025-01-15_14-32-01_fix_abc123
    """

    @property
    def _cycles_dir(self) -> Path:
        return get_workspace() / ".macrocycle" / "cycles"

    def init_cycles_dir(self) -> None:
        self._cycles_dir.mkdir(parents=True, exist_ok=True)

    def create_cycle_dir(self, macro_id: str) -> str:
        ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        suffix = secrets.token_hex(3)
        cycle_id = f"{ts}_{macro_id}_{suffix}"

        cycle_dir = self._cycles_dir / cycle_id
        (cycle_dir / "steps").mkdir(parents=True, exist_ok=True)
        return str(cycle_dir)

    def write_text(self, cycle_dir: str, rel_path: str, content: str) -> None:
        p = Path(cycle_dir) / rel_path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")

    def get_latest_cycle(self) -> CycleInfo | None:
        """Return info about the most recent cycle, or None if none exist."""
        if not self._cycles_dir.exists():
            return None

        cycle_dirs = sorted(self._cycles_dir.iterdir(), reverse=True)
        if not cycle_dirs:
            return None

        return self._parse_cycle_dir(cycle_dirs[0])

    def _parse_cycle_dir(self, path: Path) -> CycleInfo:
        """Parse a cycle directory into CycleInfo.
        
        Directory format: 2025-01-15_14-32-01_fix_abc123
        """
        name = path.name
        parts = name.split("_")

        # Parse timestamp from first two parts
        timestamp_str = f"{parts[0]}_{parts[1]}"
        started_at = datetime.strptime(timestamp_str, "%Y-%m-%d_%H-%M-%S")
        
        # macro_id is the third part
        macro_id = parts[2] if len(parts) > 2 else "unknown"

        # Count completed steps
        steps_dir = path / "steps"
        step_count = len(list(steps_dir.glob("*.md"))) if steps_dir.exists() else 0

        return CycleInfo(
            cycle_id=name,
            macro_id=macro_id,
            started_at=started_at,
            cycle_dir=str(path),
            step_count=step_count,
        )
