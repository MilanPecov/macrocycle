from macros.domain.ports.agent_port import AgentPort
from macros.infrastructure.persistence import FileMacroStore, FileCycleStore
from macros.infrastructure.runtime import CursorAgentAdapter, StdConsoleAdapter


class Container:
    """Infrastructure wiring - adapters for external systems."""

    AGENT_REGISTRY: dict[str, type] = {
        "cursor": CursorAgentAdapter,
    }

    def __init__(self, engine: str = "cursor"):
        if engine not in self.AGENT_REGISTRY:
            raise ValueError(f"Unknown engine '{engine}'. Supported: {sorted(self.AGENT_REGISTRY)}")

        self.console = StdConsoleAdapter()
        self.macro_registry = FileMacroStore()
        self.cycle_store = FileCycleStore()
        self.agent: AgentPort = self.AGENT_REGISTRY[engine](console=self.console)
