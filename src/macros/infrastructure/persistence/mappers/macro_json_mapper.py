from typing import Any, Dict

from macros.domain.model.macro import Macro


class MacroJsonMapper:
    """Bidirectional JSON mapping for Macro aggregate."""

    @staticmethod
    def from_json(text: str) -> Macro:
        return Macro.model_validate_json(text)

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> Macro:
        return Macro.model_validate(data)

    @staticmethod
    def to_json(macro: Macro) -> str:
        return macro.model_dump_json(indent=2)

    @staticmethod
    def to_dict(macro: Macro) -> Dict[str, Any]:
        return macro.model_dump()
