from enum import Enum
from datetime import datetime
from pydantic import BaseModel


class CycleStatus(str, Enum):
    """Status of a cycle execution."""
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class StepRun(BaseModel):
    """Result of executing a single step."""
    step_id: str
    started_at: datetime
    finished_at: datetime
    output_text: str
    engine: str
    exit_code: int = 0


class Cycle(BaseModel):
    """A running or completed macro execution.
    
    This is the aggregate root for cycle execution state.
    """
    cycle_id: str
    macro_id: str
    engine: str
    cycle_dir: str
    status: CycleStatus
    failure_reason: str | None = None
    started_at: datetime
    finished_at: datetime | None = None
    results: list[StepRun] = []
