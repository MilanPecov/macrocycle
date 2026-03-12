"""WorkflowValidator -- enforces definition-time invariants on Workflow aggregates."""

from macros.domain.model.workflow import Workflow, Phase
from macros.domain.model.step import LlmStep
from macros.domain.exceptions import WorkflowValidationError


class WorkflowValidator:
    """Validates a Workflow definition before execution.

    Checks:
    - At least one phase
    - Phase IDs are unique
    - Step IDs are unique within each phase
    - Transition targets (on_complete, on_exhausted) reference existing phases
    - Context dependencies reference existing phases
    - max_iterations >= 1
    - max_phase_visits >= 1
    """

    def validate(self, workflow: Workflow) -> None:
        self._validate_has_phases(workflow)
        phase_ids = self._validate_unique_phase_ids(workflow)
        self._validate_phase_internals(workflow, phase_ids)
        self._validate_global_limits(workflow)

    def _validate_has_phases(self, workflow: Workflow) -> None:
        if not workflow.phases:
            raise WorkflowValidationError(
                f"Workflow '{workflow.id}' must have at least one phase"
            )

    def _validate_unique_phase_ids(self, workflow: Workflow) -> set[str]:
        seen: set[str] = set()
        for phase in workflow.phases:
            if phase.id in seen:
                raise WorkflowValidationError(
                    f"Duplicate phase ID '{phase.id}' in workflow '{workflow.id}'"
                )
            seen.add(phase.id)
        return seen

    def _validate_phase_internals(self, workflow: Workflow, phase_ids: set[str]) -> None:
        for phase in workflow.phases:
            self._validate_unique_step_ids(phase, workflow.id)
            self._validate_transitions(phase, phase_ids, workflow.id)
            self._validate_context_refs(phase, phase_ids, workflow.id)
            self._validate_iteration_budget(phase, workflow.id)

    def _validate_unique_step_ids(self, phase: Phase, workflow_id: str) -> None:
        seen: set[str] = set()
        for step in phase.steps:
            if step.id in seen:
                raise WorkflowValidationError(
                    f"Duplicate step ID '{step.id}' in phase '{phase.id}' "
                    f"of workflow '{workflow_id}'"
                )
            seen.add(step.id)

    def _validate_transitions(
        self, phase: Phase, phase_ids: set[str], workflow_id: str
    ) -> None:
        for attr in ("on_complete", "on_exhausted"):
            target = getattr(phase, attr)
            if target is not None and target not in phase_ids:
                raise WorkflowValidationError(
                    f"Phase '{phase.id}' {attr} references unknown phase '{target}' "
                    f"in workflow '{workflow_id}'"
                )

    def _validate_context_refs(
        self, phase: Phase, phase_ids: set[str], workflow_id: str
    ) -> None:
        for dep in phase.context:
            if dep not in phase_ids:
                raise WorkflowValidationError(
                    f"Phase '{phase.id}' context dependency '{dep}' does not exist "
                    f"in workflow '{workflow_id}'"
                )

    def _validate_iteration_budget(self, phase: Phase, workflow_id: str) -> None:
        if phase.max_iterations < 1:
            raise WorkflowValidationError(
                f"Phase '{phase.id}' max_iterations must be >= 1 "
                f"in workflow '{workflow_id}'"
            )

    def _validate_global_limits(self, workflow: Workflow) -> None:
        if workflow.max_phase_visits < 1:
            raise WorkflowValidationError(
                f"Workflow '{workflow.id}' max_phase_visits must be >= 1"
            )
