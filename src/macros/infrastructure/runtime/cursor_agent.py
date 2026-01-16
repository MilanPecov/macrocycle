import subprocess

from macros.domain.ports.agent_port import AgentPort
from macros.domain.ports.console_port import ConsolePort
from macros.infrastructure.runtime.utils.workspace import get_workspace


TIMEOUT_SECONDS = 300  # Avoid hanging indefinitely


class CursorAgentAdapter(AgentPort):
    """Runs Cursor Agent CLI in "print mode".

    Cursor docs show using headless automation like:
      agent -p --force --output-format text "..."
    and that output format is controllable via --output-format (works with --print).
    """

    def __init__(self, console: ConsolePort) -> None:
        self._console = console

    def run_prompt(self, prompt: str) -> tuple[int, str]:
        cmd = [
            "agent",
            "--print",
            "--force",
            "--output-format",
            "text",
            prompt,
        ]

        try:
            proc = subprocess.run(
                cmd,
                cwd=str(get_workspace()),
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                timeout=TIMEOUT_SECONDS,
            )
            out = (proc.stdout or "").strip()
            return proc.returncode, out
        except FileNotFoundError:
            # agent binary not on PATH
            return 127, "Cursor agent CLI not found. Ensure 'agent' is on PATH."
        except subprocess.TimeoutExpired:
            return 124, "Cursor agent timed out executing prompt."
