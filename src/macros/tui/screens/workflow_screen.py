"""Workflow selection screen."""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, Static, OptionList
from textual.widgets.option_list import Option

from macros.application.usecases.list_macros import list_macros


class WorkflowScreen(Screen):
    """Select macro to apply to selected issues."""
    
    def compose(self) -> ComposeResult:
        yield Header()
        count = len(self.app.state.resolved_contexts)
        yield Static(f"Select workflow for {count} items:", id="title")
        yield OptionList(*self._build_options(), id="workflow-list")
        yield Static("⚠ Gates will be auto-approved in batch mode", id="gate-warning")
        yield Footer()
    
    def _build_options(self) -> list[Option]:
        macro_ids = list_macros(self.app.container)
        options = []
        for macro_id in macro_ids:
            try:
                macro = self.app.container.macro_registry.load_macro(macro_id)
                llm_count = sum(1 for s in macro.steps if s.type == "llm")
                gate_count = sum(1 for s in macro.steps if s.type == "gate")
                desc = f"{macro.name} - {llm_count} steps, {gate_count} gates"
                options.append(Option(desc, id=macro_id))
            except Exception:
                continue
        return options
    
    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        self.app.state.macro_id = event.option.id
        from macros.tui.screens.execution_screen import ExecutionScreen
        self.app.push_screen(ExecutionScreen())
