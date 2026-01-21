"""Build macro previews for --dry-run."""

from macros.domain.model import MacroPreview, StepPreview
from macros.domain.model.macro import Macro, LlmStep, GateStep
from macros.domain.services.template_renderer import TemplateRenderer


class PreviewBuilder:
    """Builds macro previews with rendered prompt templates."""

    def __init__(self) -> None:
        self._renderer = TemplateRenderer()

    def build(self, macro: Macro, input_text: str | None = None) -> MacroPreview:
        """Build a preview of a macro with rendered prompts."""
        variables = self._build_preview_variables(macro, input_text)

        steps = []
        for idx, step in enumerate(macro.steps, start=1):
            if isinstance(step, LlmStep):
                content = self._renderer.render(step.prompt, variables)
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
            steps=tuple(steps),
            include_previous_context=macro.include_previous_outputs,
        )

    def _build_preview_variables(self, macro: Macro, input_text: str | None) -> dict[str, str]:
        """Build template variables with placeholders for preview."""
        variables: dict[str, str] = {}

        if input_text:
            variables["INPUT"] = input_text
        else:
            variables["INPUT"] = "[← your input will appear here]"

        for step in macro.steps:
            variables[f"STEP_OUTPUT:{step.id}"] = f"[← output from: {step.id}]"

        return variables
