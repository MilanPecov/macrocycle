from typing import Protocol


class ConsolePort(Protocol):
    def info(self, msg: str) -> None:
        raise NotImplementedError

    def warn(self, msg: str) -> None:
        raise NotImplementedError

    def confirm(self, msg: str, default: bool = True) -> bool:
        raise NotImplementedError
