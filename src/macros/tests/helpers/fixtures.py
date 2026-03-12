"""Shared test fixtures and workflow builders."""

import json
from pathlib import Path

from macros.domain.model.agent_config import AgentConfig
from macros.domain.model.step import LlmStep, CommandStep
from macros.domain.model.workflow import Phase, Validation, Workflow
from macros.infrastructure.runtime.utils.workspace import set_workspace


def make_workflow(
    *,
    phases: tuple[Phase, ...] | None = None,
    workflow_id: str = "test",
    name: str = "Test Workflow",
    agent: AgentConfig | None = None,
) -> Workflow:
    """Build a Workflow with sensible defaults for testing."""
    if phases is None:
        phases = (
            Phase(
                id="default",
                steps=(LlmStep(id="s1", prompt="Do: {{INPUT}}"),),
            ),
        )
    return Workflow(
        id=workflow_id,
        name=name,
        agent=agent or AgentConfig(),
        phases=phases,
    )


def make_phase(
    phase_id: str = "test_phase",
    *,
    steps: tuple | None = None,
    max_iterations: int = 1,
    validation: Validation | None = None,
    context: tuple[str, ...] = (),
    on_complete: str | None = None,
    on_exhausted: str | None = None,
    agent: AgentConfig | None = None,
) -> Phase:
    """Build a Phase with sensible defaults for testing."""
    if steps is None:
        steps = (LlmStep(id="s1", prompt="Do: {{INPUT}}"),)
    return Phase(
        id=phase_id,
        steps=steps,
        max_iterations=max_iterations,
        validation=validation,
        context=context,
        on_complete=on_complete,
        on_exhausted=on_exhausted,
        agent=agent,
    )


SAMPLE_WORKFLOW_DICT = {
    "id": "sample",
    "name": "Sample Workflow",
    "agent": {"engine": "cursor"},
    "phases": [
        {
            "id": "analyze",
            "steps": [{"id": "s1", "type": "llm", "prompt": "Analyze: {{INPUT}}"}],
            "on_complete": "implement",
        },
        {
            "id": "implement",
            "steps": [
                {"id": "code", "type": "llm", "prompt": "Implement: {{PHASE_OUTPUT:analyze}}"},
                {"id": "test", "type": "command", "command": "pytest -q"},
            ],
            "validation": {"command": "pytest -q"},
            "max_iterations": 3,
            "context": ["analyze"],
        },
    ],
}


def init_test_workspace(path: Path) -> None:
    """Set up a test workspace."""
    (path / ".git").mkdir(parents=True, exist_ok=True)
    set_workspace(path)


def write_workflow_to_workspace(workspace: Path, workflow: dict) -> None:
    """Write a workflow JSON to the workspace."""
    wf_dir = workspace / ".macrocycle" / "workflows"
    wf_dir.mkdir(parents=True, exist_ok=True)
    (wf_dir / f"{workflow['id']}.json").write_text(json.dumps(workflow))


def init_runs_dir(workspace: Path) -> None:
    """Create the runs directory."""
    (workspace / ".macrocycle" / "runs").mkdir(parents=True, exist_ok=True)
