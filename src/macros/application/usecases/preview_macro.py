"""Preview a macro without executing."""

from macros.application.container import Container
from macros.domain.model import MacroPreview
from macros.domain.services.macro_validator import MacroValidator
from macros.application.services import PreviewBuilder


def preview_macro(
    container: Container,
    macro_id: str,
    input_text: str | None = None,
) -> MacroPreview:
    """Preview a macro with rendered prompts."""
    macro = container.macro_registry.load_macro(macro_id)
    MacroValidator().validate(macro)
    return PreviewBuilder().build(macro, input_text)
