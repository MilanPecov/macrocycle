"""Port for shell command execution (the sensor in the control loop)."""

from typing import Protocol


class CommandPort(Protocol):
    """Contract for running shell commands used as validation sensors."""

    def run_command(self, command: str, cwd: str | None = None) -> tuple[int, str]:
        """Execute a shell command. Returns (exit_code, combined_output)."""
        ...
