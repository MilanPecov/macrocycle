from macros.domain.model.macro import LlmStep
from macros.domain.model.cycle import StepRun
from macros.domain.services.template_renderer import TemplateRenderer


class PromptBuilder:
    """Builds prompts for LLM steps with context from previous steps.

    Handles:
    - Template variable substitution ({{INPUT}}, {{STEP_OUTPUT:id}})
    - Appending context from previous step outputs
    """

    def __init__(self, renderer: TemplateRenderer) -> None:
        self._renderer = renderer

    def build(
        self,
        step: LlmStep,
        input_text: str,
        previous_results: list[StepRun],
        include_previous_context: bool,
    ) -> str:
        """Build the final prompt for an LLM step.

        Args:
            step: The LLM step definition containing the prompt template
            input_text: The original user input
            previous_results: Results from prior steps
            include_previous_context: Whether to append previous outputs as context

        Returns:
            The fully rendered prompt ready for the agent
        """
        variables = self._build_variables(input_text, previous_results, step.id)
        rendered = self._renderer.render(step.prompt, variables)

        if include_previous_context and previous_results:
            context = self._format_previous_outputs(previous_results)
            rendered = f"{rendered}\n\n---\nContext from previous steps (do not ignore):\n\n{context}"

        return rendered

    def _build_variables(
        self,
        input_text: str,
        results: list[StepRun],
        current_step_id: str,
    ) -> dict[str, str]:
        """Build template variables dictionary."""
        variables: dict[str, str] = {"INPUT": input_text}
        for r in results:
            variables[f"STEP_OUTPUT:{r.step_id}"] = r.output_text
        variables[f"STEP_OUTPUT:{current_step_id}"] = ""
        return variables

    def _format_previous_outputs(self, results: list[StepRun]) -> str:
        """Format previous step outputs as readable context."""
        chunks = [
            f"## {r.step_id}\n\n{r.output_text.strip()}\n"
            for r in results
        ]
        return "\n\n---\n\n".join(chunks)
