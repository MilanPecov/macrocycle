"""Macro aggregate - workflow definition."""

from dataclasses import dataclass, field
from typing import Literal


@dataclass(frozen=True)
class LlmStep:
    """Execute a prompt via AI agent."""
    id: str
    prompt: str
    type: Literal["llm"] = field(default="llm", repr=False)


@dataclass(frozen=True)
class GateStep:
    """Pause for human approval."""
    id: str
    message: str = "Continue?"
    type: Literal["gate"] = field(default="gate", repr=False)


# Discriminated union - type field distinguishes variants
Step = LlmStep | GateStep


@dataclass(frozen=True)
class Macro:
    """A reusable workflow definition.
    
    This is the aggregate root for workflow definitions.
    Immutable once loaded.
    """
    macro_id: str
    name: str
    steps: tuple[Step, ...]  # Immutable sequence
    engine: str = "cursor"
    mode: str = "auto"
    include_previous_outputs: bool = True
