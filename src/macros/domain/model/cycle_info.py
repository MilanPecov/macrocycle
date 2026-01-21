"""Cycle summary information (read model)."""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class CycleInfo:
    """Summary information about a cycle (read model).
    
    Immutable snapshot returned by CycleStorePort.get_latest_cycle().
    """
    cycle_id: str
    macro_id: str
    started_at: datetime
    cycle_dir: str
    step_count: int
