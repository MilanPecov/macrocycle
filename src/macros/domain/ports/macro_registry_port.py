"""Port for macro registry operations."""

from typing import Protocol
from macros.domain.model.macro import Macro


class MacroRegistryPort(Protocol):
    """Contract for loading and managing macro definitions."""

    def list_macros(self) -> list[str]:
        """List all available macro IDs."""
        ...

    def load_macro(self, macro_id: str) -> Macro:
        """Load a macro by ID."""
        ...

    def init_default_macros(self) -> None:
        """Initialize default macros in the workspace."""
        ...
