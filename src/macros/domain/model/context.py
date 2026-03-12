"""ExecutionContext -- immutable snapshot passed to PhaseExecutor."""

from dataclasses import dataclass, field
from types import MappingProxyType


@dataclass(frozen=True)
class ExecutionContext:
    """Read-only snapshot of state visible to a phase execution.

    phase_outputs is deliberately a MappingProxyType to enforce immutability.
    The WorkflowExecutor builds this before each phase, filtering to only
    the outputs declared in phase.context.
    """

    input: str
    phase_outputs: MappingProxyType[str, str] = field(
        default_factory=lambda: MappingProxyType({})
    )
    iteration: int = 0
    validation_output: str | None = None
