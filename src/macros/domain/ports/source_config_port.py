"""Port for source configuration."""

from typing import Protocol
from dataclasses import dataclass


@dataclass(frozen=True)
class SourceConfig:
    """
    Configuration for connecting to a source.
    
    Value object — immutable once created.
    """
    source_id: str
    credentials: dict[str, str]
    
    def get(self, key: str, default: str | None = None) -> str | None:
        return self.credentials.get(key, default)
    
    def require(self, key: str) -> str:
        """Get required credential. Raises KeyError if missing."""
        val = self.credentials.get(key)
        if not val:
            raise KeyError(f"Missing required credential: {key}")
        return val


class SourceConfigPort(Protocol):
    """Contract for retrieving source configurations."""
    
    def get_config(self, source_id: str) -> SourceConfig | None:
        """Get config for source. None if not configured."""
        ...
    
    def get_required_credentials(self, source_id: str) -> frozenset[str]:
        """Names of required credentials for a source."""
        ...
    
    def get_missing_credentials(self, source_id: str) -> list[str]:
        """Names of missing required credentials."""
        ...
    
    def list_configured_sources(self) -> list[str]:
        """Source IDs that have valid configuration."""
        ...
