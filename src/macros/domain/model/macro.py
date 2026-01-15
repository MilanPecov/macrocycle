from typing import Literal, Annotated, Union
from pydantic import BaseModel, Field


class StepBase(BaseModel):
    """Base for all step types."""
    id: str = Field(min_length=1)


class LlmStep(StepBase):
    """Execute a prompt via AI agent."""
    type: Literal["llm"] = "llm"
    prompt: str = Field(min_length=1)


class GateStep(StepBase):
    """Pause for human approval."""
    type: Literal["gate"] = "gate"
    message: str = Field(default="Continue?")


# Discriminated union - Pydantic auto-selects by 'type' field
Step = Annotated[Union[LlmStep, GateStep], Field(discriminator="type")]


class Macro(BaseModel):
    """A reusable workflow definition."""
    macro_id: str = Field(min_length=1)    # stable identifier (filenames, CLI)
    name: str = Field(min_length=1)        # human-friendly display name
    engine: str = Field(default="cursor")  # "cursor" now, "claude_code" later
    mode: str = Field(default="auto")      # for future expansion
    include_previous_outputs: bool = True
    steps: list[Step]
