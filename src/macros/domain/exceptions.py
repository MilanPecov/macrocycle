"""Domain exceptions."""


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


class MacroNotFoundError(MacrocycleError):
    """Raised when a requested macro does not exist."""
    pass


class SourceNotFoundError(MacrocycleError):
    """Requested source doesn't exist in the registry."""
    def __init__(self, source_id: str, available: list[str]) -> None:
        self.source_id = source_id
        self.available = available
        super().__init__(
            f"Unknown source '{source_id}'. "
            f"Available: {', '.join(available) or 'none'}"
        )


class SourceNotConfiguredError(MacrocycleError):
    """Source exists but lacks required configuration."""
    def __init__(self, source_id: str, missing: list[str]) -> None:
        self.source_id = source_id
        self.missing = missing
        super().__init__(
            f"Source '{source_id}' is not configured. "
            f"Set: {', '.join(missing)}"
        )


class WorkItemNotFoundError(MacrocycleError):
    """Work item doesn't exist in the source."""
    def __init__(self, item_id: str, source_id: str) -> None:
        self.item_id = item_id
        self.source_id = source_id
        super().__init__(f"Work item '{item_id}' not found in {source_id}")
