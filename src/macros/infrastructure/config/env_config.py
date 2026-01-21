"""Environment variable based source configuration."""

import os
from macros.domain.ports.source_config_port import SourceConfig


class EnvSourceConfigAdapter:
    """
    Implements SourceConfigPort by reading environment variables.
    
    Environment variable naming convention:
    - {PROVIDER}_{KEY} -> e.g. SENTRY_AUTH_TOKEN, SENTRY_ORG, GITHUB_TOKEN
    
    Easily extensible: just add new entries to ENV_MAPPINGS.
    """
    
    # source_id -> {credential_key: (env_var, required)}
    ENV_MAPPINGS: dict[str, dict[str, tuple[str, bool]]] = {
        "sentry": {
            "token": ("SENTRY_AUTH_TOKEN", True),
            "org": ("SENTRY_ORG", True),
            "project": ("SENTRY_PROJECT", False),
            "base_url": ("SENTRY_BASE_URL", False),
        },
        "github": {
            "token": ("GITHUB_TOKEN", True),
            "owner": ("GITHUB_OWNER", True),
            "repo": ("GITHUB_REPO", True),
        },
        "jira": {
            "token": ("JIRA_API_TOKEN", True),
            "email": ("JIRA_EMAIL", True),
            "base_url": ("JIRA_BASE_URL", True),
            "project": ("JIRA_PROJECT", False),
        },
        # Add more sources here...
    }
    
    def get_config(self, source_id: str) -> SourceConfig | None:
        """Build SourceConfig from environment variables. None if any required var is missing."""
        mapping = self.ENV_MAPPINGS.get(source_id)
        if not mapping:
            return None
        
        credentials = {}
        for key, (env_var, required) in mapping.items():
            val = os.environ.get(env_var)
            if val:
                credentials[key] = val
            elif required:
                return None  # Missing required var
        
        return SourceConfig(source_id=source_id, credentials=credentials)
    
    def get_required_credentials(self, source_id: str) -> frozenset[str]:
        """Names of required credentials for a source."""
        mapping = self.ENV_MAPPINGS.get(source_id, {})
        return frozenset(
            env_var for key, (env_var, required) in mapping.items() if required
        )
    
    def get_missing_credentials(self, source_id: str) -> list[str]:
        """Return list of missing required env vars for error messages."""
        mapping = self.ENV_MAPPINGS.get(source_id, {})
        return [
            env_var for key, (env_var, required) in mapping.items()
            if required and not os.environ.get(env_var)
        ]
    
    def list_configured_sources(self) -> list[str]:
        """Source IDs that have valid configuration."""
        return [
            source_id for source_id in self.ENV_MAPPINGS
            if self.get_config(source_id) is not None
        ]
