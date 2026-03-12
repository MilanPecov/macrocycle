"""Domain exceptions."""


class MacrocycleError(Exception):
    """Base exception for all domain errors."""


class WorkflowValidationError(MacrocycleError):
    """Raised when a workflow definition is invalid."""


class WorkflowNotFoundError(MacrocycleError):
    """Raised when a requested workflow does not exist."""


class PhaseExecutionError(MacrocycleError):
    """Raised when phase execution fails unrecoverably."""
