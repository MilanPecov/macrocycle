"""Batch execution screen."""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, Static, ProgressBar
from textual.containers import VerticalScroll
from textual import work

from macros.domain.model.batch_result import BatchProgress
from macros.application.usecases.batch_fix_work_items import batch_fix_work_items


class ExecutionScreen(Screen):
    """Live progress display during batch execution."""
    
    def compose(self) -> ComposeResult:
        yield Header()
        yield Static(f"Executing {self.app.state.macro_id}...", id="title")
        yield VerticalScroll(id="progress-container")
        yield Static("Starting...", id="status")
        yield Footer()
    
    def on_mount(self) -> None:
        container = self.query_one("#progress-container", VerticalScroll)
        macro = self.app.container.macro_registry.load_macro(self.app.state.macro_id)
        self._total_steps = len(macro.steps)
        
        for ctx in self.app.state.resolved_contexts:
            item_id = ctx.item.id
            container.mount(Static(f"#{item_id} {ctx.item.title[:40]}"))
            container.mount(ProgressBar(total=self._total_steps, id=f"progress-{item_id}"))
        
        self._run_batch()
    
    @work(thread=True, exclusive=True)
    def _run_batch(self) -> None:
        result = batch_fix_work_items(
            self.app.container,
            self.app.state.resolved_contexts,
            self.app.state.macro_id,
            max_parallel=self.app.state.max_parallel,
            on_progress=self._handle_progress,
        )
        self.app.state.batch_result = result
        self.app.call_from_thread(self._go_to_summary)
    
    def _handle_progress(self, progress: BatchProgress) -> None:
        self.app.call_from_thread(self._update_progress, progress)
    
    def _update_progress(self, progress: BatchProgress) -> None:
        try:
            bar = self.query_one(f"#progress-{progress.item_id}", ProgressBar)
            bar.update(progress=progress.step_index)
        except Exception:
            pass
        self.query_one("#status", Static).update(
            f"#{progress.item_id}: Step {progress.step_index}/{progress.total_steps} - {progress.step_id}"
        )
    
    def _go_to_summary(self) -> None:
        from macros.tui.screens.summary_screen import SummaryScreen
        self.app.push_screen(SummaryScreen())
