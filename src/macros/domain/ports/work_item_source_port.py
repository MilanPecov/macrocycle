"""Port for fetching work items from external systems."""

from typing import Protocol
from macros.domain.model.work_item import WorkItem, WorkItemContext, WorkItemKind


class WorkItemSourcePort(Protocol):
    """
    Contract for work item sources.
    
    Each source (Sentry, GitHub, JIRA) implements this port.
    The port speaks DOMAIN LANGUAGE — adapters translate.
    """
    
    @property
    def source_id(self) -> str:
        """
        Unique identifier for this source.
        
        Examples: "sentry", "github", "jira", "linear"
        Used for: CLI --source flag, template lookup, config lookup
        """
        ...
    
    @property
    def supported_kinds(self) -> frozenset[WorkItemKind]:
        """
        What kinds of work items this source provides.
        
        Examples:
        - Sentry: {ERROR}
        - GitHub: {BUG, FEATURE, REVIEW}
        - JIRA: {BUG, FEATURE, TASK}
        
        Used for: Validation, filtering, UI hints
        """
        ...
    
    def discover(self, query: str, limit: int) -> list[WorkItem]:
        """
        Find work items matching query.
        
        Query syntax is SOURCE-SPECIFIC (pass-through to API):
        - Sentry: "is:unresolved age:-24h"
        - GitHub: "is:open label:bug"
        - JIRA: "project=PROJ AND status=Open"
        
        Returns: List of WorkItem, ordered by updated_at desc
        """
        ...
    
    def resolve(self, item_id: str) -> WorkItemContext:
        """
        Get full context for a work item.
        
        This is where adapters do the heavy lifting:
        1. Fetch item details from source API
        2. Fetch related data (events, comments, linked items)
        3. Map everything INTO the domain schema
        
        Raises:
            WorkItemNotFoundError: If item doesn't exist
        """
        ...
