from typing import Protocol


class CycleStorePort(Protocol):
    """Port for storing cycle artifacts."""

    def init_cycles_dir(self) -> None:
        """Ensure the cycles directory exists."""
        raise NotImplementedError

    def create_cycle_dir(self, macro_id: str) -> str:
        """Create a new cycle directory and return its path."""
        raise NotImplementedError

    def write_text(self, cycle_dir: str, rel_path: str, content: str) -> None:
        """Write text content to a file within the cycle directory."""
        raise NotImplementedError
