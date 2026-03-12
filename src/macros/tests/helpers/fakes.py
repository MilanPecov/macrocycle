"""Fake implementations of ports for testing."""

from datetime import datetime, timezone

from macros.domain.model.agent_config import AgentConfig
from macros.domain.model.run import Run, RunInfo, StepRun
from macros.domain.ports.agent_port import AgentPort
from macros.domain.ports.command_port import CommandPort
from macros.domain.ports.console_port import ConsolePort
from macros.domain.ports.run_store_port import RunStorePort


class FakeAgent:
    """Test double for AgentPort. Returns canned responses."""

    def __init__(
        self,
        text: str = "OK",
        code: int = 0,
        *,
        auto_increment: bool = False,
        responses: list[tuple[int, str]] | None = None,
    ):
        self.text = text
        self.code = code
        self.auto_increment = auto_increment
        self._responses = responses
        self.prompts: list[str] = []
        self.call_count = 0

    def run_prompt(self, prompt: str) -> tuple[int, str]:
        self.prompts.append(prompt)
        self.call_count += 1

        if self._responses and self.call_count <= len(self._responses):
            return self._responses[self.call_count - 1]

        if self.auto_increment:
            return self.code, f"Output from call {self.call_count}"

        return self.code, self.text


class FakeCommand:
    """Test double for CommandPort. Returns canned validation results."""

    def __init__(
        self,
        *,
        exit_code: int = 0,
        output: str = "",
        responses: list[tuple[int, str]] | None = None,
    ):
        self.exit_code = exit_code
        self.output = output
        self._responses = responses
        self.commands: list[str] = []
        self.call_count = 0

    def run_command(self, command: str, cwd: str | None = None) -> tuple[int, str]:
        self.commands.append(command)
        self.call_count += 1

        if self._responses and self.call_count <= len(self._responses):
            return self._responses[self.call_count - 1]

        return self.exit_code, self.output


class FakeRunStore:
    """In-memory run store for testing."""

    def __init__(self) -> None:
        self.artifacts: list[tuple[str, str, str]] = []
        self.manifests: list[Run] = []

    def create_run_dir(self, workflow_id: str) -> str:
        return f"/tmp/.macrocycle/runs/TEST_{workflow_id}"

    def write_artifact(self, run_dir: str, rel_path: str, content: str) -> None:
        self.artifacts.append((run_dir, rel_path, content))

    def save_manifest(self, run_dir: str, run: Run) -> None:
        self.manifests.append(run)

    def load_manifest(self, run_dir: str) -> Run | None:
        return self.manifests[-1] if self.manifests else None

    def get_latest_run(self) -> RunInfo | None:
        return None


class FakeConsole:
    """Silent console for testing. Captures messages."""

    def __init__(self) -> None:
        self.messages: list[str] = []

    def info(self, msg: str) -> None:
        self.messages.append(f"INFO: {msg}")

    def warn(self, msg: str) -> None:
        self.messages.append(f"WARN: {msg}")

    def echo(self, msg: str) -> None:
        self.messages.append(msg)


def make_step_run(step_id: str, output: str, exit_code: int = 0) -> StepRun:
    """Create a StepRun for testing."""
    return StepRun(
        step_id=step_id,
        phase_id="test_phase",
        iteration=1,
        started_at=datetime.now(timezone.utc),
        finished_at=datetime.now(timezone.utc),
        output=output,
        exit_code=exit_code,
    )
