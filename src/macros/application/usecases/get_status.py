from macros.application.container import Container
from macros.domain.model import CycleInfo
from macros.application.services import CycleDirParser


def get_status(container: Container) -> CycleInfo | None:
    """Return info about the most recent cycle, or None if no cycles exist."""
    cycle_dir = container.cycle_store.get_latest_cycle_dir()
    if cycle_dir is None:
        return None
    return CycleDirParser.parse(cycle_dir)
