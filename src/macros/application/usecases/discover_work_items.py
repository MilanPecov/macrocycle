"""Discover work items from a source."""

from macros.application.container import Container
from macros.application.services import get_configured_source
from macros.domain.model.work_item import WorkItem


def discover_work_items(
    container: Container,
    source_id: str,
    query: str,
    limit: int = 10,
) -> list[WorkItem]:
    """
    Find work items from a source.
    
    The query is passed through to the source — syntax is source-specific.
    """
    source = get_configured_source(container, source_id)
    return source.discover(query, limit)
