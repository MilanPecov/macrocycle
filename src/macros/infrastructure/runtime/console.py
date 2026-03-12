"""Console adapter using Rich for formatting."""

from rich.console import Console

from macros.domain.ports.console_port import ConsolePort


class StdConsoleAdapter(ConsolePort):
    """Standard console adapter using Rich."""

    def __init__(self) -> None:
        self._c = Console()

    def info(self, msg: str) -> None:
        self._c.print(f"[bold cyan]INFO[/] {msg}")

    def warn(self, msg: str) -> None:
        self._c.print(f"[bold yellow]WARN[/] {msg}")

    def echo(self, msg: str) -> None:
        self._c.print(msg)
