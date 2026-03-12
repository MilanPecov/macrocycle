"""Port for workflow definition loading."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from macros.domain.model.workflow import Workflow


class WorkflowRegistryPort(Protocol):
    """Contract for loading and managing workflow definitions."""

    def list_workflows(self) -> list[str]:
        """List all available workflow IDs."""
        ...

    def load_workflow(self, workflow_id: str) -> Workflow:
        """Load a workflow by ID. Raises WorkflowNotFoundError if missing."""
        ...

    def init_default_workflows(self) -> None:
        """Initialize default workflows in the workspace."""
        ...
