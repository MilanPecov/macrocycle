"""FileRunStore -- file-based run persistence with checkpoint manifests."""

import json
from datetime import datetime, timezone
from pathlib import Path

from macros.domain.model.run import Run, RunInfo, RunStatus, PhaseRun, StepRun
from macros.domain.model.agent_config import AgentConfig
from macros.infrastructure.runtime.utils.workspace import get_workspace


class FileRunStore:
    """Implements RunStorePort using the filesystem.

    Layout:
      .macrocycle/runs/<timestamp>_<workflow_id>/
        input.txt
        manifest.json          (checkpoint after each phase)
        <phase_id>/output.md   (phase output)
    """

    def create_run_dir(self, workflow_id: str) -> str:
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        run_dir = get_workspace() / ".macrocycle" / "runs" / f"{ts}_{workflow_id}"
        run_dir.mkdir(parents=True, exist_ok=True)
        return str(run_dir)

    def write_artifact(self, run_dir: str, rel_path: str, content: str) -> None:
        path = Path(run_dir) / rel_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def save_manifest(self, run_dir: str, run: Run) -> None:
        data = self._run_to_dict(run)
        path = Path(run_dir) / "manifest.json"
        path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")

    def load_manifest(self, run_dir: str) -> Run | None:
        path = Path(run_dir) / "manifest.json"
        if not path.exists():
            return None
        data = json.loads(path.read_text(encoding="utf-8"))
        return self._dict_to_run(data)

    def get_latest_run(self) -> RunInfo | None:
        runs_dir = get_workspace() / ".macrocycle" / "runs"
        if not runs_dir.exists():
            return None
        dirs = sorted(runs_dir.iterdir(), reverse=True)
        for d in dirs:
            if d.is_dir():
                manifest = d / "manifest.json"
                if manifest.exists():
                    data = json.loads(manifest.read_text(encoding="utf-8"))
                    return RunInfo(
                        run_id=data["id"],
                        workflow_id=data["workflow_id"],
                        started_at=datetime.fromisoformat(data["started_at"]),
                        artifacts_dir=str(d),
                        phase_count=len(data.get("phase_runs", [])),
                    )
        return None

    def _run_to_dict(self, run: Run) -> dict:
        return {
            "id": run.id,
            "workflow_id": run.workflow_id,
            "status": run.status.value,
            "started_at": run.started_at.isoformat(),
            "finished_at": run.finished_at.isoformat() if run.finished_at else None,
            "failure_reason": run.failure_reason,
            "artifacts_dir": run.artifacts_dir,
            "phase_runs": [self._phase_run_to_dict(pr) for pr in run.phase_runs],
        }

    def _phase_run_to_dict(self, pr: PhaseRun) -> dict:
        return {
            "phase_id": pr.phase_id,
            "iteration": pr.iteration,
            "outcome": pr.outcome,
            "output": pr.output,
            "validation_output": pr.validation_output,
            "started_at": pr.started_at.isoformat(),
            "finished_at": pr.finished_at.isoformat(),
            "step_runs": [self._step_run_to_dict(sr) for sr in pr.step_runs],
        }

    def _step_run_to_dict(self, sr: StepRun) -> dict:
        result: dict = {
            "step_id": sr.step_id,
            "phase_id": sr.phase_id,
            "iteration": sr.iteration,
            "started_at": sr.started_at.isoformat(),
            "finished_at": sr.finished_at.isoformat(),
            "output": sr.output,
            "exit_code": sr.exit_code,
        }
        if sr.agent_config:
            result["agent_config"] = {
                "engine": sr.agent_config.engine,
                "model": sr.agent_config.model,
            }
        return result

    def _dict_to_run(self, data: dict) -> Run:
        return Run(
            id=data["id"],
            workflow_id=data["workflow_id"],
            status=RunStatus(data["status"]),
            started_at=datetime.fromisoformat(data["started_at"]),
            finished_at=datetime.fromisoformat(data["finished_at"]) if data.get("finished_at") else None,
            failure_reason=data.get("failure_reason"),
            artifacts_dir=data.get("artifacts_dir", ""),
            phase_runs=[self._dict_to_phase_run(pr) for pr in data.get("phase_runs", [])],
        )

    def _dict_to_phase_run(self, data: dict) -> PhaseRun:
        return PhaseRun(
            phase_id=data["phase_id"],
            iteration=data["iteration"],
            outcome=data["outcome"],
            output=data.get("output", ""),
            validation_output=data.get("validation_output"),
            started_at=datetime.fromisoformat(data["started_at"]),
            finished_at=datetime.fromisoformat(data["finished_at"]),
            step_runs=tuple(self._dict_to_step_run(sr) for sr in data.get("step_runs", [])),
        )

    def _dict_to_step_run(self, data: dict) -> StepRun:
        ac = data.get("agent_config")
        return StepRun(
            step_id=data["step_id"],
            phase_id=data["phase_id"],
            iteration=data["iteration"],
            started_at=datetime.fromisoformat(data["started_at"]),
            finished_at=datetime.fromisoformat(data["finished_at"]),
            output=data.get("output", ""),
            exit_code=data.get("exit_code", 0),
            agent_config=AgentConfig(engine=ac["engine"], model=ac.get("model")) if ac else None,
        )
