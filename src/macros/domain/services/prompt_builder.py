"""PromptBuilder -- assembles prompts with variable substitution and feedback injection."""

import re

from macros.domain.model.context import ExecutionContext
from macros.domain.model.run import StepRun


_VAR_PATTERN = re.compile(r"\{\{([^}]+)\}\}")


class PromptBuilder:
    """Builds prompts for LLM steps with context from the execution state.

    Supported variables:
      {{INPUT}}                 -- original user input
      {{PHASE_OUTPUT:phase_id}} -- output from a completed phase
      {{STEP_OUTPUT:step_id}}   -- output from a prior step in the same phase
      {{ITERATION}}             -- current iteration number (1-based)
      {{VALIDATION_OUTPUT}}     -- error signal from the last validation sensor

    When iteration > 1 and validation_output is present, a feedback block
    is auto-appended to drive the agent toward convergence.
    """

    def build(
        self,
        template: str,
        context: ExecutionContext,
        step_results: list[StepRun],
        max_iterations: int = 1,
    ) -> str:
        variables = self._collect_variables(context, step_results)
        rendered = self._substitute(template, variables)

        if context.iteration > 1 and context.validation_output:
            rendered = self._append_feedback(
                rendered, context.validation_output, context.iteration, max_iterations
            )

        return rendered

    def _collect_variables(
        self,
        context: ExecutionContext,
        step_results: list[StepRun],
    ) -> dict[str, str]:
        variables: dict[str, str] = {
            "INPUT": context.input,
            "ITERATION": str(context.iteration),
        }

        if context.validation_output is not None:
            variables["VALIDATION_OUTPUT"] = context.validation_output

        for phase_id, output in context.phase_outputs.items():
            variables[f"PHASE_OUTPUT:{phase_id}"] = output

        for sr in step_results:
            variables[f"STEP_OUTPUT:{sr.step_id}"] = sr.output

        return variables

    def _substitute(self, template: str, variables: dict[str, str]) -> str:
        def replacer(match: re.Match) -> str:
            key = match.group(1)
            return variables.get(key, match.group(0))

        return _VAR_PATTERN.sub(replacer, template)

    def _append_feedback(
        self,
        prompt: str,
        validation_output: str,
        iteration: int,
        max_iterations: int,
    ) -> str:
        feedback = (
            f"\n\n--- Validation Failed (attempt {iteration}/{max_iterations}) ---\n"
            f"{validation_output.strip()}\n"
            f"--- Fix the issues above and try again ---"
        )
        return prompt + feedback
