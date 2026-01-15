from macros.domain.services.template_renderer import TemplateRenderer
from macros.domain.services.prompt_builder import PromptBuilder
from macros.domain.ports.agent_port import AgentPort

from macros.infrastructure.runtime import CursorAgentAdapter, StdConsoleAdapter
from macros.infrastructure.persistence import FileMacroStore, FileCycleStore


class Container:
    """Dependency injection container for the application."""

    AGENT_REGISTRY: dict[str, type] = {
        "cursor": CursorAgentAdapter,
    }

    def __init__(self, engine: str = "cursor"):
        if engine not in self.AGENT_REGISTRY:
            raise ValueError(f"Unknown engine '{engine}'. Supported: {sorted(self.AGENT_REGISTRY)}")

        # Create all dependencies - workspace is a global constant, not passed
        self.console = StdConsoleAdapter()
        self.renderer = TemplateRenderer()
        self.prompt_builder = PromptBuilder(self.renderer)
        self.macro_registry = FileMacroStore()
        self.cycle_store = FileCycleStore()
        self.agent: AgentPort = self.AGENT_REGISTRY[engine](console=self.console)
