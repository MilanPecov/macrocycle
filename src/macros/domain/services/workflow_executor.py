"""WorkflowExecutor -- outer control loop: sequences phases, manages context."""

from datetime import datetime, timezone
from types import MappingProxyType

from macros.domain.model.context import ExecutionContext
from macros.domain.model.run import Run, RunStatus
from macros.domain.model.workflow import Workflow
from macros.domain.ports.console_port import ConsolePort
from macros.domain.ports.run_store_port import RunStorePort
from macros.domain.services.phase_executor import PhaseExecutor


class WorkflowExecutor:
    """Outer control loop: navigates the workflow graph, delegates to PhaseExecutor.

    Responsibilities:
    - Phase sequencing via on_complete / on_exhausted transitions
    - Context accumulation and filtering per phase.context declarations
    - Checkpoint persistence after each phase (manifest)
    - Global safety limit via max_phase_visits
    """

    def __init__(
        self,
        phase_executor: PhaseExecutor,
        store: RunStorePort,
        console: ConsolePort,
    ) -> None:
        self._phase_executor = phase_executor
        self._store = store
        self._console = console

    def execute(
        self,
        workflow: Workflow,
        input_text: str,
        *,
        stop_after: str | None = None,
    ) -> Run:
        run_dir = self._store.create_run_dir(workflow.id)
        run = Run(
            id=run_dir.rsplit("/", 1)[-1],
            workflow_id=workflow.id,
            status=RunStatus.RUNNING,
            started_at=datetime.now(timezone.utc),
            artifacts_dir=run_dir,
        )
        self._store.write_artifact(run_dir, "input.txt", input_text)

        self._console.info(f"Workflow: {workflow.name} ({workflow.agent.engine})")
        self._console.info(f"Artifacts: {run_dir}")

        phase_index = {p.id: p for p in workflow.phases}
        accumulated_outputs: dict[str, str] = {}
        visit_count = 0
        current_phase_id: str | None = workflow.phases[0].id

        while current_phase_id is not None:
            visit_count += 1
            if visit_count > workflow.max_phase_visits:
                run.status = RunStatus.FAILED
                run.failure_reason = (
                    f"Exceeded max_phase_visits ({workflow.max_phase_visits})"
                )
                break

            phase = phase_index[current_phase_id]
            self._console.info(f"Phase: {phase.id}")

            context = self._build_context(
                input_text, phase.context, accumulated_outputs
            )

            phase_run = self._phase_executor.execute(
                phase, context, workflow.agent
            )
            run.phase_runs.append(phase_run)

            rel_path = f"{phase.id}/output.md"
            self._store.write_artifact(run_dir, rel_path, phase_run.output)
            self._store.save_manifest(run_dir, run)

            accumulated_outputs[phase.id] = phase_run.output

            self._console.info(
                f"Phase {phase.id}: {phase_run.outcome} "
                f"(iter {phase_run.iteration})"
            )

            if stop_after == phase.id:
                self._console.warn(f"Stopping after --until {stop_after}")
                break

            if phase_run.outcome == "converged":
                current_phase_id = phase.on_complete
            elif phase_run.outcome == "exhausted":
                current_phase_id = phase.on_exhausted
            else:
                run.status = RunStatus.FAILED
                run.failure_reason = (
                    f"Phase '{phase.id}' failed at iteration {phase_run.iteration}"
                )
                break
        else:
            pass

        if run.status == RunStatus.RUNNING:
            run.status = RunStatus.COMPLETED

        run.finished_at = datetime.now(timezone.utc)
        self._store.save_manifest(run_dir, run)
        return run

    def _build_context(
        self,
        input_text: str,
        context_deps: tuple[str, ...],
        accumulated: dict[str, str],
    ) -> ExecutionContext:
        if context_deps:
            filtered = {k: v for k, v in accumulated.items() if k in context_deps}
        else:
            filtered = dict(accumulated)

        return ExecutionContext(
            input=input_text,
            phase_outputs=MappingProxyType(filtered),
            iteration=1,
        )
