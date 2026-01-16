from datetime import datetime
from pathlib import Path
import secrets

from macros.domain.ports.cycle_store_port import CycleStorePort
from macros.infrastructure.runtime.utils.workspace import get_workspace


class FileCycleStore(CycleStorePort):
    """Cycle artifact storage."""

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

    def get_latest_cycle_dir(self) -> str | None:
        if not self._cycles_dir.exists():
            return None

        cycle_dirs = sorted(self._cycles_dir.iterdir(), reverse=True)
        if not cycle_dirs:
            return None

        return str(cycle_dirs[0])
