"""Source selection screen."""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, Static, OptionList
from textual.widgets.option_list import Option


class SourceScreen(Screen):
    """Select a work item source."""
    
    def compose(self) -> ComposeResult:
        yield Header()
        yield Static("Select a source:", id="title")
        yield OptionList(*self._build_options(), id="source-list")
        yield Static("", id="setup-hint")
        yield Footer()
    
    def _build_options(self) -> list[Option]:
        registry = self.app.container.source_registry
        config = self.app.container.source_config
        configured = set(config.list_configured_sources())
        options = []
        for source_id in registry.list_sources():
            is_configured = source_id in configured
            status = "✓ Connected" if is_configured else "✗ Not configured"
            label = f"{source_id.title():<20} {status}"
            options.append(Option(label, id=source_id, disabled=not is_configured))
        return options
    
    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        source_id = event.option.id
        self.app.state.source_id = source_id
        self.app.state.default_query = self.app.container.source_registry.get_default_query(source_id)
        from macros.tui.screens.issues_screen import IssuesScreen
        self.app.push_screen(IssuesScreen())
    
    def on_option_list_option_highlighted(self, event: OptionList.OptionHighlighted) -> None:
        source_id = event.option.id
        config = self.app.container.source_config
        if source_id not in config.list_configured_sources():
            missing = config.get_missing_credentials(source_id)
            hint = f"Setup: export {' '.join(f'{v}=...' for v in missing)}"
        else:
            hint = ""
        self.query_one("#setup-hint", Static).update(hint)
