"""Main Textual application."""

from textual.app import App
from textual.binding import Binding

from macros.application.container import Container
from macros.tui.state import TuiState


class MacrocycleApp(App):
    """Interactive TUI for batch work item processing."""
    
    TITLE = "macrocycle"
    
    CSS = """
    Screen { align: center middle; }
    #title { text-style: bold; margin-bottom: 1; }
    OptionList { height: auto; max-height: 15; margin: 1 0; }
    SelectionList { height: auto; max-height: 15; margin: 1 0; }
    #setup-hint { color: $warning; margin-top: 1; }
    #selection-count { margin-top: 1; }
    #gate-warning { color: $warning; margin-top: 1; }
    #status { margin-top: 1; }
    ProgressBar { margin: 0 0 1 0; }
    #progress-container { height: auto; max-height: 20; }
    #results { height: auto; }
    LoadingIndicator { height: 3; }
    """
    
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("escape", "go_back", "Back"),
    ]
    
    def __init__(self) -> None:
        super().__init__()
        self.container = Container()
        self.state = TuiState()
    
    def on_mount(self) -> None:
        from macros.tui.screens.source_screen import SourceScreen
        self.push_screen(SourceScreen())
    
    def action_go_back(self) -> None:
        if len(self.screen_stack) > 1:
            self.pop_screen()
