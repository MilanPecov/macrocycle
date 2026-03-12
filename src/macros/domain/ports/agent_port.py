"""Port for AI agent execution."""

from typing import Callable, Protocol


class AgentPort(Protocol):
    """Contract for executing prompts via an AI agent (the actuator)."""

    def run_prompt(self, prompt: str) -> tuple[int, str]:
        """Execute a prompt and return (exit_code, output_text)."""
        ...
