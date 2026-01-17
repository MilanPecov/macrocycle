import subprocess

from macros.domain.ports.agent_port import AgentPort
from macros.domain.ports.console_port import ConsolePort
from macros.infrastructure.runtime.utils.workspace import get_workspace


TIMEOUT_SECONDS = 300  # Avoid hanging indefinitely


class CursorAgentAdapter(AgentPort):
    """Runs Cursor Agent CLI in "print mode".

    Cursor docs show using headless automation like:
      agent -p --force --output-format text "..."
    """

    def __init__(
        self,
        console: ConsolePort,
        binary: str = "agent",
        extra_args: list[str] | None = None,
        timeout: int = TIMEOUT_SECONDS,
    ) -> None:
        self._console = console
        self._binary = binary
        self._extra_args = extra_args or []
        self._timeout = timeout

    def run_prompt(self, prompt: str) -> tuple[int, str]:
        cmd = [
            self._binary,
            "--print",
            "--force",
            "--output-format",
            "text",
            *self._extra_args,
            prompt,
        ]

        try:
            proc = subprocess.run(
                cmd,
                cwd=str(get_workspace()),
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                timeout=self._timeout,
            )
            out = (proc.stdout or "").strip()
            return proc.returncode, out
        except FileNotFoundError:
            return 127, f"Agent binary '{self._binary}' not found. Ensure it's on PATH."
        except subprocess.TimeoutExpired:
            return 124, f"Agent timed out after {self._timeout}s."
