"""Shared test doubles for ports."""

from macros.domain.model import CycleInfo
from macros.domain.ports.agent_port import AgentPort
from macros.domain.ports.cycle_store_port import CycleStorePort
from macros.domain.ports.console_port import ConsolePort


class FakeAgent(AgentPort):
    """Test double that returns canned responses."""

    def __init__(self, text: str = "OK", code: int = 0):
        self.text = text
        self.code = code
        self.prompts: list[str] = []

    def run_prompt(self, prompt: str) -> tuple[int, str]:
        self.prompts.append(prompt)
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
