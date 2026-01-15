from macros.domain.ports.console_port import ConsolePort
from rich.console import Console
import typer


class StdConsoleAdapter(ConsolePort):
    """Standard console adapter using Rich for formatting and Typer for prompts."""

    def __init__(self):
        self._c = Console()

    def info(self, msg: str) -> None:
        self._c.print(f"[bold cyan]INFO[/] {msg}")

    def warn(self, msg: str) -> None:
        self._c.print(f"[bold yellow]WARN[/] {msg}")

    def confirm(self, msg: str, default: bool = True) -> bool:
        return typer.confirm(msg, default=default)
