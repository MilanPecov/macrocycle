"""Shared state across TUI screens."""

from dataclasses import dataclass, field
from macros.domain.model.work_item import WorkItem, WorkItemContext
from macros.domain.model.batch_result import BatchResult


@dataclass
class TuiState:
    """Mutable state passed between screens."""
    source_id: str | None = None
    work_items: list[WorkItem] = field(default_factory=list)
    selected_ids: set[str] = field(default_factory=set)
    resolved_contexts: list[WorkItemContext] = field(default_factory=list)
    macro_id: str | None = None
    batch_result: BatchResult | None = None
    max_selection: int = 10
    max_parallel: int = 5
    default_query: str = ""
