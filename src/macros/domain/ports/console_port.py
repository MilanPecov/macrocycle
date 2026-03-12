"""Port for console output operations."""

from typing import Protocol


class ConsolePort(Protocol):
    """Contract for console I/O."""

    def info(self, msg: str) -> None: ...
    def warn(self, msg: str) -> None: ...
    def echo(self, msg: str) -> None: ...
