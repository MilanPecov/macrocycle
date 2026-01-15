from typing import Protocol
from macros.domain.model.macro import Macro


class MacroRegistryPort(Protocol):
    """Port for loading and managing macro definitions."""

    def list_macros(self) -> list[str]:
        """List all available macro IDs."""
        raise NotImplementedError

    def load_macro(self, macro_id: str) -> Macro:
        """Load a macro by ID."""
        raise NotImplementedError

    def init_default_macros(self) -> None:
        """Initialize default macros in the workspace."""
        raise NotImplementedError
