"""Batch fix work items use case."""

from __future__ import annotations
from typing import TYPE_CHECKING, Callable, Sequence

from macros.domain.model.work_item import WorkItemContext
from macros.domain.model.batch_result import BatchProgress, BatchResult
from macros.application.services.batch_orchestrator import BatchOrchestrator, BatchItem
from macros.domain.services.macro_validator import MacroValidator

if TYPE_CHECKING:
    from macros.application.container import Container


def batch_fix_work_items(
    container: Container,
    contexts: Sequence[WorkItemContext],
    macro_id: str,
    max_parallel: int = 5,
    on_progress: Callable[[BatchProgress], None] | None = None,
) -> BatchResult:
    """Execute a macro on multiple work items in parallel."""
    macro = container.macro_registry.load_macro(macro_id)
    MacroValidator().validate(macro)
    
    renderer = container.work_item_renderer
    batch_items = [
        BatchItem(
            item_id=ctx.item.id,
            item_title=ctx.item.title,
            input_text=renderer.render(ctx),
        )
        for ctx in contexts
    ]
    
    orchestrator = BatchOrchestrator(
        agent_factory=container.create_agent,
        cycle_store=container.cycle_store,
        console=container.console,
    )
    
    return orchestrator.run(batch_items, macro, max_parallel, on_progress)
