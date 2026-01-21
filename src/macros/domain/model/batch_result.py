"""Batch execution result types."""

from dataclasses import dataclass
from typing import Literal

from macros.domain.model.cycle import Cycle


@dataclass(frozen=True)
class BatchProgress:
    """Progress update emitted during batch execution."""
    item_id: str
    item_title: str
    step_index: int
    total_steps: int
    step_id: str
    step_type: Literal["llm", "gate"]
    status: Literal["started", "completed", "failed"]


@dataclass(frozen=True)
class BatchItemResult:
    """Result for a single work item in a batch."""
    item_id: str
    item_title: str
    cycle: Cycle | None = None
    error: str | None = None


@dataclass(frozen=True)
class BatchResult:
    """Aggregated result of batch execution."""
    items: tuple[BatchItemResult, ...]
    elapsed_seconds: float
    
    @property
    def succeeded(self) -> tuple[BatchItemResult, ...]:
        return tuple(r for r in self.items if r.error is None)
    
    @property
    def failed(self) -> tuple[BatchItemResult, ...]:
        return tuple(r for r in self.items if r.error is not None)
