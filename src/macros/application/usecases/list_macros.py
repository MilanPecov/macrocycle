"""List available macros use case."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from macros.application.container import Container


def list_macros(container: Container) -> list[str]:
    """List all available macro IDs."""
    return container.macro_registry.list_macros()
