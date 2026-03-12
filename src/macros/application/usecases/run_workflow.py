"""Use case: run a workflow."""

from macros.application.container import Container
from macros.domain.model.run import Run


def run_workflow(
    container: Container,
    workflow_id: str,
    input_text: str,
    *,
    stop_after: str | None = None,
) -> Run:
    workflow = container.workflow_registry.load_workflow(workflow_id)
    executor = container.workflow_executor()
    return executor.execute(workflow, input_text, stop_after=stop_after)
