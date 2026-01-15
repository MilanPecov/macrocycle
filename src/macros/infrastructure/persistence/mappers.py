from typing import Any, Dict

from macros.domain.model.macro import Macro


class MacroJsonMapper:
    """Bidirectional JSON mapping for Macro aggregate.

    Thin wrappers around Pydantic to make mapping explicit and testable.
    """

    @staticmethod
    def from_json(text: str) -> Macro:
        """Parse JSON text into a Macro domain object."""
        return Macro.model_validate_json(text)

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> Macro:
        """Convert a dictionary into a Macro domain object."""
        return Macro.model_validate(data)

    @staticmethod
    def to_json(macro: Macro) -> str:
        """Serialize a Macro to JSON text."""
        return macro.model_dump_json(indent=2)

    @staticmethod
    def to_dict(macro: Macro) -> Dict[str, Any]:
        """Convert a Macro to a dictionary."""
        return macro.model_dump()
