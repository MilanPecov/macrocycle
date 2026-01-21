"""Macro preview models (read models)."""

from dataclasses import dataclass


@dataclass(frozen=True)
class StepPreview:
    """Preview of a single step (immutable)."""
    index: int
    step_id: str
    step_type: str
    content: str


@dataclass(frozen=True)
class MacroPreview:
    """Full preview of a macro with rendered prompts (read model).
    
    Immutable snapshot used for --dry-run display.
    """
    name: str
    engine: str
    steps: tuple[StepPreview, ...]  # Immutable sequence
    include_previous_context: bool
