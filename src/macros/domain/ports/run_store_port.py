"""Port for run artifact persistence and checkpointing."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from macros.domain.model.run import Run, RunInfo


class RunStorePort(Protocol):
    """Contract for persisting run state and artifacts."""

    def create_run_dir(self, workflow_id: str) -> str:
        """Create a new run directory and return its path."""
        ...

    def write_artifact(self, run_dir: str, rel_path: str, content: str) -> None:
        """Write text content to a file within the run directory."""
        ...

    def save_manifest(self, run_dir: str, run: Run) -> None:
        """Save run manifest for crash recovery (checkpoint)."""
        ...

    def load_manifest(self, run_dir: str) -> Run | None:
        """Load run manifest. Returns None if no manifest exists."""
        ...

    def get_latest_run(self) -> RunInfo | None:
        """Return info about the most recent run, or None."""
        ...
