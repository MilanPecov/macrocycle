"""Workflow aggregate -- the definition-time graph of phases."""

from dataclasses import dataclass

from macros.domain.model.agent_config import AgentConfig
from macros.domain.model.step import Step


@dataclass(frozen=True)
class Validation:
    """Sensor configuration: a shell command whose exit code signals convergence."""

    command: str


@dataclass(frozen=True)
class Phase:
    """A single control loop within a workflow.

    Each phase executes its steps, optionally validates via a shell command,
    and iterates until convergence (exit_code == 0) or budget exhaustion.
    """

    id: str
    steps: tuple[Step, ...]
    max_iterations: int = 1
    validation: Validation | None = None
    context: tuple[str, ...] = ()
    agent: AgentConfig | None = None
    on_complete: str | None = None
    on_exhausted: str | None = None


@dataclass(frozen=True)
class Workflow:
    """Aggregate root: a directed graph of phases with a default agent config.

    Invariants:
    - At least one phase
    - Phase IDs are unique
    - Transition targets reference existing phases
    - max_phase_visits prevents infinite traversal
    """

    id: str
    name: str
    agent: AgentConfig
    phases: tuple[Phase, ...]
    max_phase_visits: int = 50
