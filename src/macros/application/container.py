"""Container wires infrastructure adapters to domain ports."""

from macros.domain.model.agent_config import AgentConfig
from macros.domain.ports.agent_port import AgentPort
from macros.domain.services.phase_executor import AgentFactory
from macros.domain.services.prompt_builder import PromptBuilder
from macros.domain.services.phase_executor import PhaseExecutor
from macros.domain.services.workflow_executor import WorkflowExecutor
from macros.infrastructure.persistence import FileRunStore, FileWorkflowStore
from macros.infrastructure.runtime import (
    CursorAgentAdapter,
    StdConsoleAdapter,
    SubprocessCommandAdapter,
)


class Container:
    """Infrastructure wiring -- adapters for external systems."""

    AGENT_REGISTRY: dict[str, type] = {
        "cursor": CursorAgentAdapter,
    }

    def __init__(self, engine: str = "cursor"):
        if engine not in self.AGENT_REGISTRY:
            raise ValueError(
                f"Unknown engine '{engine}'. Supported: {sorted(self.AGENT_REGISTRY)}"
            )
        self._engine = engine
        self.console = StdConsoleAdapter()
        self.workflow_registry = FileWorkflowStore()
        self.run_store = FileRunStore()
        self.command = SubprocessCommandAdapter()

    def agent_factory(self) -> AgentFactory:
        """Returns a factory that creates agent instances from AgentConfig."""
        cls = self.AGENT_REGISTRY[self._engine]
        console = self.console

        def factory(config: AgentConfig) -> AgentPort:
            return cls(console=console)

        return factory

    def workflow_executor(self) -> WorkflowExecutor:
        """Build the fully wired workflow executor."""
        prompt_builder = PromptBuilder()
        phase_executor = PhaseExecutor(
            agent_factory=self.agent_factory(),
            command=self.command,
            prompt_builder=prompt_builder,
            console=self.console,
        )
        return WorkflowExecutor(
            phase_executor=phase_executor,
            store=self.run_store,
            console=self.console,
        )
