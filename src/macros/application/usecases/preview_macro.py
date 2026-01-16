import re
from dataclasses import dataclass

from macros.application.container import Container
from macros.domain.model.macro import Macro, LlmStep, GateStep


@dataclass
class StepPreview:
    """Preview of a single step."""
    index: int
    step_id: str
    step_type: str
    content: str  # Rendered prompt or gate message


@dataclass
class MacroPreview:
    """Full preview of a macro with rendered prompts."""
    name: str
    engine: str
    steps: list[StepPreview]
    include_previous_context: bool


def preview_macro(
    container: Container,
    macro_id: str,
    input_text: str | None = None,
) -> MacroPreview:
    """Preview a macro with rendered prompts.
    
    Args:
        container: Application container
        macro_id: The macro to preview
        input_text: Optional input to render into prompts
        
    Returns:
        MacroPreview with all steps and their rendered content
    """
    macro = container.macro_registry.load_macro(macro_id)
    
    steps = []
    for idx, step in enumerate(macro.steps, start=1):
        if isinstance(step, LlmStep):
            content = _render_preview_prompt(step.prompt, input_text, macro)
            steps.append(StepPreview(
                index=idx,
                step_id=step.id,
                step_type="llm",
                content=content,
            ))
        elif isinstance(step, GateStep):
            steps.append(StepPreview(
                index=idx,
                step_id=step.id,
                step_type="gate",
                content=step.message,
            ))
    
    return MacroPreview(
        name=macro.name,
        engine=macro.engine,
        steps=steps,
        include_previous_context=macro.include_previous_outputs,
    )


def _render_preview_prompt(template: str, input_text: str | None, macro: Macro) -> str:
    """Render a prompt template for preview.
    
    - {{INPUT}} → actual input or placeholder
    - {{STEP_OUTPUT:step_id}} → placeholder showing dependency
    """
    result = template
    
    # Replace {{INPUT}}
    if input_text:
        result = result.replace("{{INPUT}}", input_text)
    else:
        result = result.replace("{{INPUT}}", "[← your input will appear here]")
    
    # Replace {{STEP_OUTPUT:step_id}} with readable placeholders
    def replace_step_ref(match: re.Match) -> str:
        step_id = match.group(1)
        return f"[← output from: {step_id}]"
    
    result = re.sub(r"\{\{STEP_OUTPUT:(\w+)\}\}", replace_step_ref, result)
    
    return result
