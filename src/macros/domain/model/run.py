"""Run aggregate -- mutable execution state."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Literal

from macros.domain.model.agent_config import AgentConfig


class RunStatus(str, Enum):
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class StepRun:
    """Record of a single step execution within a phase iteration."""

    step_id: str
    phase_id: str
    iteration: int
    started_at: datetime
    finished_at: datetime
    output: str
    exit_code: int
    agent_config: AgentConfig | None = None


@dataclass
class PhaseRun:
    """Record of a complete phase execution (possibly multiple iterations)."""

    phase_id: str
    iteration: int
    outcome: Literal["converged", "exhausted", "failed"]
    step_runs: tuple[StepRun, ...]
    output: str
    validation_output: str | None
    started_at: datetime
    finished_at: datetime


@dataclass
class RunInfo:
    """Summary of a run (read model for status display)."""

    run_id: str
    workflow_id: str
    started_at: datetime
    artifacts_dir: str
    phase_count: int


@dataclass
class Run:
    """Aggregate root for workflow execution state.

    Mutable: phase_runs is append-only during execution.
    """

    id: str
    workflow_id: str
    status: RunStatus
    phase_runs: list[PhaseRun] = field(default_factory=list)
    started_at: datetime = field(default_factory=lambda: datetime.min)
    finished_at: datetime | None = None
    failure_reason: str | None = None
    artifacts_dir: str = ""
