"""Batch completion summary."""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, Static
from textual.containers import VerticalScroll
from textual.binding import Binding

from macros.tui.state import TuiState


class SummaryScreen(Screen):
    """Display batch results."""
    
    BINDINGS = [
        Binding("n", "new_batch", "New Batch"),
        Binding("q", "quit", "Exit"),
    ]
    
    def compose(self) -> ComposeResult:
        yield Header()
        yield Static("Batch Complete", id="title")
        yield VerticalScroll(id="results")
        yield Footer()
    
    def on_mount(self) -> None:
        result = self.app.state.batch_result
        container = self.query_one("#results", VerticalScroll)
        
        if result is None:
            container.mount(Static("No results available"))
            return
        
        succeeded = result.succeeded
        failed = result.failed
        
        container.mount(Static(f"✓ Succeeded: {len(succeeded)}"))
        for item_result in succeeded:
            if item_result.cycle:
                container.mount(Static(f"  → {item_result.cycle.cycle_dir}"))
        
        container.mount(Static(f"✗ Failed: {len(failed)}"))
        for item_result in failed:
            container.mount(Static(f"  → {item_result.error}"))
        
        container.mount(Static(f"\nTotal time: {result.elapsed_seconds:.1f}s"))
    
    def action_new_batch(self) -> None:
        self.app.state = TuiState()
        while len(self.app.screen_stack) > 1:
            self.app.pop_screen()
        self.app.pop_screen()
        from macros.tui.screens.source_screen import SourceScreen
        self.app.push_screen(SourceScreen())
