"""Cycle aggregate - execution state for a macro run."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class CycleStatus(str, Enum):
    """Status of a cycle execution."""
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass(frozen=True)
class StepRun:
    """Immutable record of executing a single step."""
    step_id: str
    started_at: datetime
    finished_at: datetime
    output_text: str
    engine: str
    exit_code: int = 0


@dataclass
class Cycle:
    """A running or completed macro execution.
    
    This is the aggregate root for cycle execution state.
    """
    cycle_id: str
    macro_id: str
    engine: str
    cycle_dir: str
    status: CycleStatus
    started_at: datetime
    failure_reason: str | None = None
    finished_at: datetime | None = None
    results: list[StepRun] = field(default_factory=list)
