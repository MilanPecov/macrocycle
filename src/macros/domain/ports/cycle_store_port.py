from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from macros.domain.model import CycleInfo


class CycleStorePort(Protocol):
    """Port for cycle artifact storage and retrieval."""

    def init_cycles_dir(self) -> None:
        """Ensure the cycles directory exists."""
        ...

    def create_cycle_dir(self, macro_id: str) -> str:
        """Create a new cycle directory and return its path."""
        ...

    def write_text(self, cycle_dir: str, rel_path: str, content: str) -> None:
        """Write text content to a file within the cycle directory."""
        ...

    def get_latest_cycle(self) -> "CycleInfo | None":
        """Return info about the most recent cycle, or None if none exist."""
        ...
