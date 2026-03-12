"""FileWorkflowStore -- loads workflow definitions from JSON files."""

import json
from importlib import resources
from pathlib import Path

from macros.domain.exceptions import WorkflowNotFoundError
from macros.domain.model.agent_config import AgentConfig
from macros.domain.model.step import CommandStep, LlmStep, Step
from macros.domain.model.workflow import Phase, Validation, Workflow
from macros.domain.services.workflow_validator import WorkflowValidator
from macros.infrastructure.runtime.utils.workspace import get_workspace


class FileWorkflowStore:
    """Implements WorkflowRegistryPort using JSON files on disk.

    Looks for workflows in:
      1. .macrocycle/workflows/<id>.json (local, takes precedence)
      2. Packaged defaults (bundled with the package)
    """

    def __init__(self) -> None:
        self._validator = WorkflowValidator()

    def list_workflows(self) -> list[str]:
        local = self._local_dir()
        if not local.exists():
            return []
        return sorted(p.stem for p in local.glob("*.json"))

    def load_workflow(self, workflow_id: str) -> Workflow:
        data = self._load_json(workflow_id)
        if data is None:
            raise WorkflowNotFoundError(f"Workflow not found: {workflow_id}")
        workflow = self._parse_workflow(data)
        self._validator.validate(workflow)
        return workflow

    def init_default_workflows(self) -> None:
        local = self._local_dir()
        local.mkdir(parents=True, exist_ok=True)
        (get_workspace() / ".macrocycle" / "runs").mkdir(parents=True, exist_ok=True)

        defaults_pkg = resources.files("macros.infrastructure.persistence.defaults")
        for item in defaults_pkg.iterdir():
            if item.name.endswith(".json"):
                target = local / item.name
                if not target.exists():
                    target.write_text(item.read_text(encoding="utf-8"), encoding="utf-8")

    def _local_dir(self) -> Path:
        return get_workspace() / ".macrocycle" / "workflows"

    def _load_json(self, workflow_id: str) -> dict | None:
        local_path = self._local_dir() / f"{workflow_id}.json"
        if local_path.exists():
            return json.loads(local_path.read_text(encoding="utf-8"))

        try:
            defaults_pkg = resources.files("macros.infrastructure.persistence.defaults")
            resource = defaults_pkg.joinpath(f"{workflow_id}.json")
            return json.loads(resource.read_text(encoding="utf-8"))
        except (FileNotFoundError, TypeError):
            return None

    def _parse_workflow(self, data: dict) -> Workflow:
        agent_data = data.get("agent", {})
        agent = AgentConfig(
            engine=agent_data.get("engine", "cursor"),
            model=agent_data.get("model"),
        )

        phases = tuple(self._parse_phase(p) for p in data.get("phases", []))

        return Workflow(
            id=data["id"],
            name=data.get("name", data["id"]),
            agent=agent,
            phases=phases,
            max_phase_visits=data.get("max_phase_visits", 50),
        )

    def _parse_phase(self, data: dict) -> Phase:
        steps = tuple(self._parse_step(s) for s in data.get("steps", []))

        validation = None
        if "validation" in data:
            validation = Validation(command=data["validation"]["command"])

        agent = None
        if "agent" in data:
            agent = AgentConfig(
                engine=data["agent"].get("engine", "cursor"),
                model=data["agent"].get("model"),
            )

        return Phase(
            id=data["id"],
            steps=steps,
            max_iterations=data.get("max_iterations", 1),
            validation=validation,
            context=tuple(data.get("context", [])),
            agent=agent,
            on_complete=data.get("on_complete"),
            on_exhausted=data.get("on_exhausted"),
        )

    def _parse_step(self, data: dict) -> Step:
        step_type = data.get("type", "llm")
        if step_type == "command":
            return CommandStep(id=data["id"], command=data["command"])

        agent = None
        if "agent" in data:
            agent = AgentConfig(
                engine=data["agent"].get("engine", "cursor"),
                model=data["agent"].get("model"),
            )
        return LlmStep(
            id=data["id"],
            prompt=data["prompt"],
            agent=agent,
        )
