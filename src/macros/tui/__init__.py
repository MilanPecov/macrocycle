"""Terminal UI for interactive batch processing."""

from macros.tui.app import MacrocycleApp


def run_tui() -> None:
    """Launch the interactive TUI."""
    app = MacrocycleApp()
    app.run()


__all__ = ["run_tui"]
