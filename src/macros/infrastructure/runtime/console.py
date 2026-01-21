"""Console I/O adapter using Rich and Typer."""

import typer
from rich.console import Console

from macros.domain.ports.console_port import ConsolePort


class StdConsoleAdapter(ConsolePort):
    """Standard console adapter using Rich for formatting and Typer for prompts."""

    def __init__(self):
        self._c = Console()

    def info(self, msg: str) -> None:
        self._c.print(f"[bold cyan]INFO[/] {msg}")

    def warn(self, msg: str) -> None:
        self._c.print(f"[bold yellow]WARN[/] {msg}")

    def echo(self, msg: str) -> None:
        self._c.print(msg)

    def confirm(self, msg: str, default: bool = True) -> bool:
        return typer.confirm(msg, default=default)
