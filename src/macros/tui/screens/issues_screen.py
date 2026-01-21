"""Issue selection screen."""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, Static, SelectionList, Input, LoadingIndicator
from textual.binding import Binding
from textual.worker import Worker
from textual import work

from macros.application.usecases.discover_work_items import discover_work_items
from macros.application.services.source_registry import get_configured_source


class IssuesScreen(Screen):
    """Multi-select issues from the configured source."""
    
    BINDINGS = [
        Binding("a", "select_all", "Select All"),
        Binding("n", "select_none", "Clear"),
        Binding("enter", "continue", "Continue"),
    ]
    
    def compose(self) -> ComposeResult:
        yield Header()
        yield Static(f"Issues from {self.app.state.source_id}", id="title")
        yield Input(placeholder="Filter query...", id="query-input")
        yield LoadingIndicator(id="loader")
        yield SelectionList[str](id="issue-list")
        yield Static("", id="selection-count")
        yield Footer()
    
    def on_mount(self) -> None:
        self.query_one("#query-input", Input).value = self.app.state.default_query
        self._fetch_issues()
    
    @work(thread=True)
    def _fetch_issues(self) -> list:
        return discover_work_items(
            self.app.container,
            self.app.state.source_id,
            self.app.state.default_query,
            limit=50,
        )
    
    def on_worker_state_changed(self, event: Worker.StateChanged) -> None:
        if event.state.name == "SUCCESS":
            items = event.worker.result
            self.app.state.work_items = items
            self._populate_list(items)
            self.query_one("#loader", LoadingIndicator).display = False
        elif event.state.name == "ERROR":
            self.notify(f"Error: {event.worker.error}", severity="error")
            self.query_one("#loader", LoadingIndicator).display = False
    
    def _populate_list(self, items: list) -> None:
        selection_list = self.query_one("#issue-list", SelectionList)
        selection_list.clear_options()
        for item in items:
            label = f"[{item.kind.value}] #{item.id} {item.title[:50]}"
            selection_list.add_option((label, item.id))
        self._update_count()
    
    def on_selection_list_selected_changed(self, event) -> None:
        selection_list = self.query_one("#issue-list", SelectionList)
        selected = list(selection_list.selected)
        if len(selected) > self.app.state.max_selection:
            selection_list.deselect(selected[-1])
            self.notify(f"Maximum {self.app.state.max_selection} items", severity="warning")
        self._update_count()
    
    def _update_count(self) -> None:
        selection_list = self.query_one("#issue-list", SelectionList)
        count = len(list(selection_list.selected))
        self.query_one("#selection-count", Static).update(f"Selected: {count} / {self.app.state.max_selection} max")
    
    def action_select_all(self) -> None:
        selection_list = self.query_one("#issue-list", SelectionList)
        selection_list.select_all()
        selected = list(selection_list.selected)
        if len(selected) > self.app.state.max_selection:
            for item_id in selected[self.app.state.max_selection:]:
                selection_list.deselect(item_id)
        self._update_count()
    
    def action_select_none(self) -> None:
        self.query_one("#issue-list", SelectionList).deselect_all()
        self._update_count()
    
    def action_continue(self) -> None:
        """Resolve selected items and continue to workflow screen."""
        selection_list = self.query_one("#issue-list", SelectionList)
        selected_ids = set(selection_list.selected)
        if not selected_ids:
            self.notify("Select at least one issue", severity="warning")
            return
        self.app.state.selected_ids = selected_ids
        self.query_one("#loader", LoadingIndicator).display = True
        self._resolve_contexts()
    
    @work(thread=True)
    def _resolve_contexts(self) -> None:
        source = get_configured_source(self.app.container, self.app.state.source_id)
        contexts = []
        for item_id in self.app.state.selected_ids:
            try:
                contexts.append(source.resolve(item_id))
            except Exception as e:
                self.app.call_from_thread(self.notify, f"Failed: {item_id}", severity="warning")
        self.app.state.resolved_contexts = contexts
        self.app.call_from_thread(self._go_to_workflow)
    
    def _go_to_workflow(self) -> None:
        self.query_one("#loader", LoadingIndicator).display = False
        if not self.app.state.resolved_contexts:
            self.notify("No items resolved", severity="error")
            return
        from macros.tui.screens.workflow_screen import WorkflowScreen
        self.app.push_screen(WorkflowScreen())
