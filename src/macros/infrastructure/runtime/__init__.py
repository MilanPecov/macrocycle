from .cursor_agent import CursorAgentAdapter
from .console import StdConsoleAdapter
from macros.infrastructure.runtime.utils.workspace import get_workspace, set_workspace
from macros.infrastructure.runtime.utils.input_service import resolve_input

__all__ = [
    "CursorAgentAdapter",
    "StdConsoleAdapter",
    "get_workspace",
    "set_workspace",
    "resolve_input",
]
