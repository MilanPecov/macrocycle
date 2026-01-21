"""Main Textual application."""

from textual.app import App
from textual.binding import Binding

from macros.application.container import Container
from macros.tui.state import TuiState


class MacrocycleApp(App):
    """Interactive TUI for batch work item processing."""
    
    TITLE = "macrocycle"
    
    CSS = """
    Screen {
        background: $surface;
    }
    
    /* Title bar */
    #title {
        text-style: bold;
        color: $text;
        padding: 1 2;
        background: $primary;
        width: 100%;
        text-align: center;
    }
    
    #subtitle {
        color: $text-muted;
        padding: 1 2;
        text-align: center;
    }
    
    /* Option list styling */
    OptionList {
        height: auto;
        max-height: 10;
        margin: 1 4;
        border: round $primary;
        background: $surface;
        padding: 1;
    }
    
    OptionList:focus {
        border: round $accent;
    }
    
    OptionList > .option-list--option-highlighted {
        background: $primary 30%;
        text-style: bold;
    }
    
    OptionList > .option-list--option-disabled {
        color: $text-muted;
    }
    
    /* Setup hint box */
    #setup-box {
        border: round $warning 50%;
        margin: 1 4;
        padding: 1 2;
        background: $surface-darken-1;
        height: auto;
        max-height: 15;
    }
    
    #setup-title {
        margin-bottom: 1;
    }
    
    #setup-cmd {
        padding-left: 2;
    }
    
    /* Selection list */
    SelectionList {
        height: auto;
        max-height: 15;
        margin: 1 4;
        border: round $primary;
        background: $surface;
        padding: 1;
    }
    
    SelectionList:focus {
        border: round $accent;
    }
    
    /* Selection count */
    #selection-count {
        color: $accent;
        padding: 1 4;
        text-style: bold;
    }
    
    /* Gate warning */
    #gate-warning {
        color: $text;
        padding: 1 2;
        background: $warning 15%;
        margin: 1 4;
        border: round $warning 50%;
        text-align: center;
    }
    
    /* Status line */
    #status {
        color: $accent;
        padding: 1 4;
        text-style: italic;
    }
    
    /* Progress bars */
    ProgressBar {
        margin: 0 4 1 4;
    }
    
    ProgressBar Bar {
        color: $success;
    }
    
    #progress-container {
        height: auto;
        max-height: 20;
        margin: 1 4;
        padding: 1 2;
        border: round $primary;
    }
    
    /* Results container */
    #results {
        height: auto;
        margin: 1 4;
        padding: 1 2;
        border: round $primary;
    }
    
    /* Utility classes */
    .success { color: $success; }
    .error { color: $error; }
    .warning { color: $warning; }
    .muted { color: $text-muted; }
    
    /* Loading indicator */
    LoadingIndicator {
        height: 3;
        color: $accent;
    }
    
    /* Input fields */
    Input {
        margin: 1 4;
        border: round $primary;
    }
    
    Input:focus {
        border: round $accent;
    }
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
