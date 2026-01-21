"""Input resolution for CLI commands."""

from pathlib import Path
import sys


def resolve_input(text: str | None, file: str | None) -> str | None:
    """
    Resolve input from argument, file, or stdin.
    
    This is an application service that prepares input for use cases.
    
    Priority:
    1. Explicit "-" means read from stdin
    2. If no text/file provided and stdin has data, read stdin
    3. If file provided, read from file
    4. Otherwise return text as-is
    """
    if text == "-" or (text is None and file is None and not sys.stdin.isatty()):
        return sys.stdin.read().strip() or None
    if file:
        return Path(file).read_text(encoding="utf-8")
    return text
