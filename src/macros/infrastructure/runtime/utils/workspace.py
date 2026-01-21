"""Workspace root discovery and management."""

from pathlib import Path

_workspace: Path | None = None


def get_workspace() -> Path:
    """Get the workspace root (lazy singleton).
    
    Discovers the workspace on first call, then caches it.
    """
    global _workspace
    if _workspace is None:
        _workspace = _discover_workspace()
    return _workspace


def set_workspace(path: Path | str | None) -> None:
    """Override the workspace (for testing)."""
    global _workspace
    _workspace = Path(path) if path else None


def _discover_workspace() -> Path:
    """Find the workspace root by walking up the directory tree.

    Heuristic: walk up until we find .git or .macrocycle, otherwise use cwd.
    """
    p = Path.cwd().resolve()
    for _ in range(20):
        if (p / ".git").exists() or (p / ".macrocycle").exists():
            return p
        if p.parent == p:
            break
        p = p.parent
    return Path.cwd().resolve()
