"""Container wires infrastructure adapters."""

from pathlib import Path

from macros.domain.ports.agent_port import AgentPort
from macros.infrastructure.persistence import FileMacroStore, FileCycleStore
from macros.infrastructure.runtime import CursorAgentAdapter, StdConsoleAdapter, WorkItemRenderer
from macros.infrastructure.sources import SentrySourceAdapter, GitHubSourceAdapter
from macros.infrastructure.config import EnvSourceConfigAdapter
from macros.application.services.source_registry import SourceRegistry
from macros.infrastructure.runtime.utils.workspace import get_workspace


class Container:
    """Infrastructure wiring - adapters for external systems."""

    AGENT_REGISTRY: dict[str, type] = {
        "cursor": CursorAgentAdapter,
    }

    def __init__(self, engine: str = "cursor"):
        if engine not in self.AGENT_REGISTRY:
            raise ValueError(f"Unknown engine '{engine}'. Supported: {sorted(self.AGENT_REGISTRY)}")

        self._engine = engine
        self.console = StdConsoleAdapter()
        self.macro_registry = FileMacroStore()
        self.cycle_store = FileCycleStore()
        self.agent: AgentPort = self.AGENT_REGISTRY[engine](console=self.console)

        self.source_config = EnvSourceConfigAdapter()
        self.source_registry = self._build_source_registry()
        self.work_item_renderer = self._build_work_item_renderer()

    def create_agent(self) -> AgentPort:
        """Create a new agent instance for batch execution."""
        return self.AGENT_REGISTRY[self._engine](console=self.console)

    def _build_source_registry(self) -> SourceRegistry:
        """Wire up available work item sources with their default queries."""
        registry = SourceRegistry()
        registry.register("sentry", SentrySourceAdapter, default_query="is:unresolved")
        registry.register("github", GitHubSourceAdapter, default_query="is:open")
        return registry

    def _build_work_item_renderer(self) -> WorkItemRenderer:
        """Create WorkItemRenderer with template paths."""
        workspace = Path(get_workspace())
        package_templates = Path(__file__).parent.parent / "infrastructure" / "templates"
        return WorkItemRenderer(workspace, package_templates)
