"""Parallel batch execution of macros across work items."""

import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Callable, Sequence

from macros.domain.model.macro import Macro
from macros.domain.model.cycle import Cycle
from macros.domain.model.batch_result import BatchProgress, BatchResult, BatchItemResult
from macros.domain.ports.agent_port import AgentPort
from macros.domain.ports.cycle_store_port import CycleStorePort
from macros.domain.ports.console_port import ConsolePort
from macros.domain.services.cycle_orchestrator import CycleOrchestrator


@dataclass(frozen=True)
class BatchItem:
    """Input item for batch execution."""
    item_id: str
    item_title: str
    input_text: str


ProgressCallback = Callable[[BatchProgress], None]


class BatchOrchestrator:
    """Execute a macro on multiple items in parallel.
    
    Threading model:
    - ThreadPoolExecutor with configurable max_workers (1-10)
    - Each worker gets its own CycleOrchestrator + AgentPort
    - Progress callbacks invoked from worker threads
    - Graceful shutdown via threading.Event on KeyboardInterrupt
    """
    
    def __init__(
        self,
        agent_factory: Callable[[], AgentPort],
        cycle_store: CycleStorePort,
        console: ConsolePort,
    ) -> None:
        self._agent_factory = agent_factory
        self._cycle_store = cycle_store
        self._console = console
        self._shutdown = threading.Event()
    
    def run(
        self,
        items: Sequence[BatchItem],
        macro: Macro,
        max_parallel: int = 5,
        on_progress: ProgressCallback | None = None,
    ) -> BatchResult:
        """Execute macro on all items, returning aggregated results."""
        max_parallel = max(1, min(10, max_parallel))
        start_time = time.monotonic()
        results: list[BatchItemResult] = []
        
        with ThreadPoolExecutor(max_workers=max_parallel) as executor:
            future_to_item = {
                executor.submit(self._execute_single, item, macro, on_progress): item
                for item in items
            }
            
            try:
                for future in as_completed(future_to_item):
                    item = future_to_item[future]
                    try:
                        cycle = future.result()
                        results.append(BatchItemResult(
                            item_id=item.item_id,
                            item_title=item.item_title,
                            cycle=cycle,
                        ))
                    except Exception as e:
                        results.append(BatchItemResult(
                            item_id=item.item_id,
                            item_title=item.item_title,
                            error=str(e),
                        ))
            except KeyboardInterrupt:
                self._shutdown.set()
                executor.shutdown(wait=False, cancel_futures=True)
                # Mark remaining futures as cancelled
                for future, item in future_to_item.items():
                    if not future.done():
                        results.append(BatchItemResult(
                            item_id=item.item_id,
                            item_title=item.item_title,
                            error="Cancelled by user",
                        ))
        
        return BatchResult(items=tuple(results), elapsed_seconds=time.monotonic() - start_time)
    
    def _execute_single(
        self,
        item: BatchItem,
        macro: Macro,
        on_progress: ProgressCallback | None,
    ) -> Cycle:
        """Execute macro on single item. Runs in worker thread."""
        if self._shutdown.is_set():
            raise RuntimeError("Batch cancelled")
        
        agent = self._agent_factory()
        orchestrator = CycleOrchestrator(
            agent=agent,
            cycle_store=self._cycle_store,
            console=self._console,
        )
        
        def step_callback(step_idx: int, total: int, step_id: str, step_type: str) -> None:
            if on_progress and not self._shutdown.is_set():
                on_progress(BatchProgress(
                    item_id=item.item_id,
                    item_title=item.item_title,
                    step_index=step_idx,
                    total_steps=total,
                    step_id=step_id,
                    step_type=step_type,  # type: ignore
                    status="started",
                ))
        
        return orchestrator.run(
            macro=macro,
            input_text=item.input_text,
            auto_approve=True,
            on_step_start=step_callback,
        )
