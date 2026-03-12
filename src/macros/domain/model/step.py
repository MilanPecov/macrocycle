"""Step types -- the individual actions within a phase."""

from dataclasses import dataclass
from typing import Literal, Union

from macros.domain.model.agent_config import AgentConfig


@dataclass(frozen=True)
class LlmStep:
    """Execute a prompt via an AI agent (the actuator)."""

    id: str
    prompt: str
    type: Literal["llm"] = "llm"
    agent: AgentConfig | None = None


@dataclass(frozen=True)
class CommandStep:
    """Execute a shell command (can serve as inline sensor or action)."""

    id: str
    command: str
    type: Literal["command"] = "command"


Step = Union[LlmStep, CommandStep]
