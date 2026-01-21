"""Registry for work item sources."""

from __future__ import annotations
from typing import Callable, TYPE_CHECKING
from macros.domain.ports.work_item_source_port import WorkItemSourcePort
from macros.domain.ports.source_config_port import SourceConfig
from macros.domain.exceptions import SourceNotFoundError, SourceNotConfiguredError

if TYPE_CHECKING:
    from macros.application.container import Container


def get_configured_source(container: Container, source_id: str) -> WorkItemSourcePort:
    """
    Validate source exists and is configured, then create adapter.
    
    Raises:
        SourceNotFoundError: If source_id is not registered
        SourceNotConfiguredError: If required credentials are missing
    """
    if not container.source_registry.has_source(source_id):
        raise SourceNotFoundError(source_id, container.source_registry.list_sources())
    
    config = container.source_config.get_config(source_id)
    if not config:
        missing = container.source_config.get_missing_credentials(source_id)
        raise SourceNotConfiguredError(source_id, missing)
    
    return container.source_registry.create_source(source_id, config)


class SourceRegistry:
    """
    Maps source IDs to factory functions and metadata.
    
    Factory signature: (config: SourceConfig) -> WorkItemSourcePort
    
    This is the application's knowledge of which sources exist.
    Adding a new source = register it here with its default query.
    """
    
    def __init__(self) -> None:
        self._factories: dict[str, Callable[[SourceConfig], WorkItemSourcePort]] = {}
        self._default_queries: dict[str, str] = {}
    
    def register(
        self,
        source_id: str,
        factory: Callable[[SourceConfig], WorkItemSourcePort],
        default_query: str = "",
    ) -> None:
        self._factories[source_id] = factory
        self._default_queries[source_id] = default_query
    
    def create_source(self, source_id: str, config: SourceConfig) -> WorkItemSourcePort:
        if source_id not in self._factories:
            raise SourceNotFoundError(source_id, self.list_sources())
        return self._factories[source_id](config)
    
    def list_sources(self) -> list[str]:
        return sorted(self._factories.keys())
    
    def has_source(self, source_id: str) -> bool:
        return source_id in self._factories
    
    def get_default_query(self, source_id: str) -> str:
        return self._default_queries.get(source_id, "")
