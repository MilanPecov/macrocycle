"""Use case: initialize the workspace."""

from macros.application.container import Container


def init_workspace(container: Container) -> None:
    container.workflow_registry.init_default_workflows()
