"""Resolve work item context and run appropriate macro."""

from macros.application.container import Container
from macros.application.services import get_configured_source
from macros.application.usecases.run_macro import run_macro
from macros.domain.model.cycle import Cycle


def fix_work_item(
    container: Container,
    source_id: str,
    item_id: str,
    *,
    macro_id: str | None = None,
    yes: bool = False,
    until: str | None = None,
) -> Cycle:
    """
    Resolve work item, render context, run macro.
    
    1. Validate source and get adapter
    2. Resolve item to full context
    3. Render context to LLM input text
    4. Run macro (uses suggested_macro unless overridden)
    """
    source = get_configured_source(container, source_id)
    context = source.resolve(item_id)

    input_text = container.work_item_renderer.render(context)
    actual_macro = macro_id or context.suggested_macro

    return run_macro(container, actual_macro, input_text, yes=yes, until=until)
