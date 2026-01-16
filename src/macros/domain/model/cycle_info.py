from dataclasses import dataclass
from datetime import datetime


@dataclass
class CycleInfo:
    """Summary information about a cycle (read model)."""
    cycle_id: str
    macro_id: str
    started_at: datetime
    cycle_dir: str
    step_count: int
