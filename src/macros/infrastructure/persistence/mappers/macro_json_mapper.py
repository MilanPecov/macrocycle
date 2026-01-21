"""JSON mapping for Macro aggregate."""

import json
from typing import Any

from macros.domain.model.macro import Macro, LlmStep, GateStep, Step


class MacroJsonMapper:
    """Bidirectional JSON mapping for Macro aggregate.
    
    Handles the discriminated union of Step types via the 'type' field.
    """

    @staticmethod
    def from_json(text: str) -> Macro:
        data = json.loads(text)
        return MacroJsonMapper.from_dict(data)

    @staticmethod
    def from_dict(data: dict[str, Any]) -> Macro:
        steps = tuple(MacroJsonMapper._parse_step(s) for s in data.get("steps", []))
        return Macro(
            macro_id=data["macro_id"],
            name=data["name"],
            steps=steps,
            engine=data.get("engine", "cursor"),
            mode=data.get("mode", "auto"),
            include_previous_outputs=data.get("include_previous_outputs", True),
        )

    @staticmethod
    def _parse_step(data: dict[str, Any]) -> Step:
        """Parse a step dict into the appropriate Step type."""
        step_type = data.get("type", "llm")
        if step_type == "gate":
            return GateStep(
                id=data["id"],
                message=data.get("message", "Continue?"),
            )
        # Default to LlmStep
        return LlmStep(
            id=data["id"],
            prompt=data["prompt"],
        )

    @staticmethod
    def to_json(macro: Macro) -> str:
        return json.dumps(MacroJsonMapper.to_dict(macro), indent=2)

    @staticmethod
    def to_dict(macro: Macro) -> dict[str, Any]:
        return {
            "macro_id": macro.macro_id,
            "name": macro.name,
            "engine": macro.engine,
            "mode": macro.mode,
            "include_previous_outputs": macro.include_previous_outputs,
            "steps": [MacroJsonMapper._step_to_dict(s) for s in macro.steps],
        }

    @staticmethod
    def _step_to_dict(step: Step) -> dict[str, Any]:
        """Convert a Step to dict."""
        if isinstance(step, GateStep):
            return {"id": step.id, "type": "gate", "message": step.message}
        # LlmStep
        return {"id": step.id, "type": "llm", "prompt": step.prompt}
