"""Use case: list available workflows."""

from macros.application.container import Container


def list_workflows(container: Container) -> list[str]:
    return container.workflow_registry.list_workflows()
