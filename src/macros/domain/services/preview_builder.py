import re

from macros.domain.model import MacroPreview, StepPreview
from macros.domain.model.macro import Macro, LlmStep, GateStep


class PreviewBuilder:
    """Builds macro previews with rendered prompt templates."""

    def build(self, macro: Macro, input_text: str | None = None) -> MacroPreview:
        """Build a preview of a macro with rendered prompts."""
        steps = []
        for idx, step in enumerate(macro.steps, start=1):
            if isinstance(step, LlmStep):
                content = self._render_prompt(step.prompt, input_text)
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

    def _render_prompt(self, template: str, input_text: str | None) -> str:
        """Render a prompt template for preview with placeholders."""
        result = template

        if input_text:
            result = result.replace("{{INPUT}}", input_text)
        else:
            result = result.replace("{{INPUT}}", "[← your input will appear here]")

        def replace_step_ref(match: re.Match) -> str:
            step_id = match.group(1)
            return f"[← output from: {step_id}]"

        result = re.sub(r"\{\{STEP_OUTPUT:(\w+)\}\}", replace_step_ref, result)

        return result
