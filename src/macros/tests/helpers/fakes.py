"""Fake implementations of ports for testing."""

from datetime import datetime, timezone
from pathlib import Path

from macros.domain.model import CycleInfo
from macros.domain.model.cycle import StepRun
from macros.domain.ports.agent_port import AgentPort
from macros.domain.ports.cycle_store_port import CycleStorePort
from macros.domain.ports.console_port import ConsolePort


# =============================================================================
# Factories
# =============================================================================

def make_step_run(step_id: str, output: str, exit_code: int = 0) -> StepRun:
    """Create a StepRun for testing with minimal boilerplate."""
    return StepRun(
        step_id=step_id,
        started_at=datetime.now(timezone.utc),
        finished_at=datetime.now(timezone.utc),
        output_text=output,
        engine="cursor",
        exit_code=exit_code,
    )


# =============================================================================
# Fakes
# =============================================================================

class FakeAgent(AgentPort):
    """Test double that returns canned responses.
    
    Can be configured with:
    - Fixed text/code for all calls (backward compatible)
    - Auto-incrementing output for context verification
    """

    def __init__(
        self,
        text: str = "OK",
        code: int = 0,
        *,
        auto_increment: bool = False,
    ):
        self.text = text
        self.code = code
        self.auto_increment = auto_increment
        self.prompts: list[str] = []
        self.call_count = 0

    def run_prompt(self, prompt: str) -> tuple[int, str]:
        self.prompts.append(prompt)
        self.call_count += 1
        
        if self.auto_increment:
            # Return distinct output per call for context verification
            return self.code, f"Output from step {self.call_count}"
        
        return self.code, self.text


class FakeCycleStore(CycleStorePort):
    """In-memory cycle store for testing."""

    def __init__(self):
        self.writes: list[tuple[str, str, str]] = []

    def init_cycles_dir(self) -> None:
        pass

    def create_cycle_dir(self, macro_id: str) -> str:
        return f"/tmp/.macrocycle/cycles/TEST_{macro_id}"

    def write_text(self, cycle_dir: str, rel_path: str, content: str) -> None:
        self.writes.append((cycle_dir, rel_path, content))

    def get_latest_cycle(self) -> CycleInfo | None:
        return None


class FakeConsole(ConsolePort):
    """Silent console for testing."""

    def __init__(self, approve: bool = True):
        self._approve = approve

    def info(self, msg: str) -> None:
        pass

    def warn(self, msg: str) -> None:
        pass

    def echo(self, msg: str) -> None:
        pass

    def confirm(self, msg: str, default: bool = True) -> bool:
        return self._approve
