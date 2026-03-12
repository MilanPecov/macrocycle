from .cursor_agent import CursorAgentAdapter
from .console import StdConsoleAdapter
from .subprocess_command import SubprocessCommandAdapter
from macros.infrastructure.runtime.utils.workspace import get_workspace, set_workspace
from macros.infrastructure.runtime.utils.input_resolver import resolve_input

__all__ = [
    "CursorAgentAdapter",
    "StdConsoleAdapter",
    "SubprocessCommandAdapter",
    "get_workspace",
    "set_workspace",
    "resolve_input",
]
