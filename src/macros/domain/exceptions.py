class MacrocycleError(Exception):
    """Base exception for all domain errors."""
    pass


class MacroValidationError(MacrocycleError):
    """Raised when a macro definition is invalid.
    
    Examples:
    - Duplicate step IDs
    - Invalid step references
    - Missing required fields
    """
    pass


class CycleExecutionError(MacrocycleError):
    """Raised when cycle execution fails.
    
    Examples:
    - Agent failure
    - Step execution error
    - User cancellation
    """
    pass


class MacroNotFoundError(MacrocycleError):
    """Raised when a requested macro does not exist."""
    pass
