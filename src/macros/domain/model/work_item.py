"""
WorkItem domain model.

These are VALUE OBJECTS — immutable snapshots of external state.
Identity is owned by the source system, not by us.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class WorkItemKind(Enum):
    """
    Classification of work items.
    
    Domain defines the vocabulary; adapters map source-specific
    types into these categories.
    """
    ERROR = "error"      # Runtime errors: Sentry, Rollbar, Bugsnag
    BUG = "bug"          # Bug reports: GitHub issue, JIRA bug
    FEATURE = "feature"  # Feature requests: GitHub issue, JIRA story
    TASK = "task"        # Tasks: JIRA task, Asana task, Linear issue
    INCIDENT = "incident"  # Alerts: PagerDuty, Opsgenie
    REVIEW = "review"    # Code review: GitHub PR, GitLab MR


class WorkItemStatus(Enum):
    """
    Normalized status across all sources.
    
    Adapters map source-specific statuses (Sentry's "unresolved",
    GitHub's "open", JIRA's "To Do") into these.
    """
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    CLOSED = "closed"


@dataclass(frozen=True)
class WorkItem:
    """
    A unit of work from an external system.
    
    Contains only UNIVERSAL fields that exist across all sources.
    This is what appears in list views.
    
    Invariants:
    - id is non-empty (enforced by source)
    - source matches the adapter that created it
    - url is a valid link back to the source
    """
    id: str
    source: str
    kind: WorkItemKind
    title: str
    status: WorkItemStatus
    url: str
    created_at: datetime
    updated_at: datetime
    
    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("WorkItem.id cannot be empty")
        if not self.source:
            raise ValueError("WorkItem.source cannot be empty")


@dataclass(frozen=True)
class StackFrame:
    """
    A single frame in a stack trace.
    
    Domain model — adapters translate source-specific formats
    (Sentry's nested entries, Python tracebacks, JS stack strings)
    into this normalized shape.
    """
    filename: str
    function: str
    lineno: int
    code: str | None = None          # The actual line of code
    context_before: tuple[str, ...] = ()  # Lines before
    context_after: tuple[str, ...] = ()   # Lines after


@dataclass(frozen=True)
class Comment:
    """A comment on a work item."""
    author: str
    body: str
    created_at: datetime


@dataclass(frozen=True)
class LinkedItem:
    """A reference to a related item (PR, issue, commit)."""
    kind: str      # "pr", "issue", "commit", "branch"
    id: str
    title: str
    url: str
    status: str | None = None


@dataclass(frozen=True)
class WorkItemContext:
    """
    Full context for acting on a work item.
    
    The SCHEMA is domain-defined. Adapters MUST populate these fields
    (even if None). Templates can rely on the structure.
    
    Design rationale:
    - Typed fields over dict[str, Any] = templates don't guess at keys
    - Optional fields over required = sources provide what they have
    - extras dict = escape hatch for truly source-specific data
    """
    # === Core (always present) ===
    item: WorkItem
    
    # === Common Optional Fields ===
    # Most sources have these; None if not available
    description: str | None = None
    assignees: tuple[str, ...] = ()
    labels: tuple[str, ...] = ()
    priority: str | None = None     # "critical", "high", "medium", "low"
    project: str | None = None      # Project/repo name
    
    # === Structured Sections ===
    # Domain-defined shapes for complex data
    stacktrace: tuple[StackFrame, ...] = ()   # For errors
    comments: tuple[Comment, ...] = ()         # Discussion thread
    linked_items: tuple[LinkedItem, ...] = ()  # Related PRs, issues
    
    # === Source-Specific Extras ===
    # Escape hatch for data that doesn't fit the schema
    # Templates can access via extras.get("key")
    extras: dict[str, Any] = field(default_factory=dict)
    
    # === Rendering Hints ===
    suggested_macro: str = "fix"   # Which macro makes sense for this item
    
    @property
    def has_stacktrace(self) -> bool:
        return len(self.stacktrace) > 0
    
    @property
    def has_comments(self) -> bool:
        return len(self.comments) > 0
