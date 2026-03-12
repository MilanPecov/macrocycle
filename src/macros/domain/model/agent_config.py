"""AgentConfig value object -- controls which engine/model executes a step."""

from dataclasses import dataclass


@dataclass(frozen=True)
class AgentConfig:
    """Immutable configuration for an AI agent.

    Supports a three-level cascade: Workflow -> Phase -> Step.
    Each level can override the parent's config.
    """

    engine: str = "cursor"
    model: str | None = None


def resolve_agent_config(
    step_agent: AgentConfig | None,
    phase_agent: AgentConfig | None,
    workflow_agent: AgentConfig,
) -> AgentConfig:
    """Resolve agent config using step -> phase -> workflow cascade.

    The most specific non-None config wins. Within a config,
    individual fields fall through to the parent level.
    """
    base = workflow_agent
    if phase_agent is not None:
        base = AgentConfig(
            engine=phase_agent.engine or base.engine,
            model=phase_agent.model if phase_agent.model is not None else base.model,
        )
    if step_agent is not None:
        base = AgentConfig(
            engine=step_agent.engine or base.engine,
            model=step_agent.model if step_agent.model is not None else base.model,
        )
    return base
