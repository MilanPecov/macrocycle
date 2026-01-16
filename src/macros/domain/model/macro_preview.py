from dataclasses import dataclass


@dataclass
class StepPreview:
    """Preview of a single step."""
    index: int
    step_id: str
    step_type: str
    content: str


@dataclass
class MacroPreview:
    """Full preview of a macro with rendered prompts (read model)."""
    name: str
    engine: str
    steps: list[StepPreview]
    include_previous_context: bool
