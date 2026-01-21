"""Port for AI agent execution."""

from typing import Protocol


class AgentPort(Protocol):
    """Contract for executing prompts via an AI agent."""

    def run_prompt(self, prompt: str) -> tuple[int, str]:
        """Execute a prompt and return (exit_code, output_text)."""
        raise NotImplementedError
