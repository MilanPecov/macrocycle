"""Get cycle status use case."""

from macros.application.container import Container
from macros.domain.model import CycleInfo


def get_status(container: Container) -> CycleInfo | None:
    """Return info about the most recent cycle, or None if no cycles exist."""
    return container.cycle_store.get_latest_cycle()
