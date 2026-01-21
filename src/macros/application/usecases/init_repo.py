"""Initialize macrocycle in a workspace."""

from macros.application.container import Container


def init_repo(container: Container) -> None:
    """Initialize the macrocycle workspace with default macros."""
    container.macro_registry.init_default_macros()
    container.cycle_store.init_cycles_dir()
