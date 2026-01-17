import unittest

from macros.domain.model.macro import LlmStep
from macros.domain.services.prompt_builder import PromptBuilder
from macros.domain.services.template_renderer import TemplateRenderer
from macros.tests.helpers import make_step_run


class TestPromptBuilder(unittest.TestCase):
    """Tests for the PromptBuilder service.
    
    PromptBuilder handles:
    - Template variable substitution ({{INPUT}}, {{STEP_OUTPUT:id}})
    - Previous step context assembly
    """

    def setUp(self):
        self.renderer = TemplateRenderer()
        self.builder = PromptBuilder(self.renderer)

    # -------------------------------------------------------------------------
    # Variable Substitution
    # -------------------------------------------------------------------------

    def test_substitutes_input_variable(self):
        # GIVEN a prompt template with {{INPUT}}
        step = LlmStep(id="s1", prompt="Process: {{INPUT}}")

        # WHEN building the prompt with user input
        result = self.builder.build(
            step=step,
            input_text="Hello World",
            previous_results=[],
            include_previous_context=False,
        )

        # THEN the variable is replaced with the input
        self.assertEqual(result, "Process: Hello World")

    def test_substitutes_step_output_variable(self):
        # GIVEN a previous step's output
        prev = make_step_run("analyze", "Analysis complete")
        step = LlmStep(id="s2", prompt="Based on: {{STEP_OUTPUT:analyze}}")

        # WHEN building the prompt
        result = self.builder.build(
            step=step,
            input_text="ignored",
            previous_results=[prev],
            include_previous_context=False,
        )

        # THEN the step output variable is replaced
        self.assertEqual(result, "Based on: Analysis complete")

    def test_unknown_variables_kept_as_is(self):
        # GIVEN a prompt with an unknown variable
        step = LlmStep(id="s1", prompt="{{UNKNOWN}} and {{INPUT}}")

        # WHEN building the prompt
        result = self.builder.build(
            step=step,
            input_text="X",
            previous_results=[],
            include_previous_context=False,
        )

        # THEN unknown variables remain, known ones are replaced
        self.assertEqual(result, "{{UNKNOWN}} and X")

    # -------------------------------------------------------------------------
    # Context Assembly
    # -------------------------------------------------------------------------

    def test_appends_previous_context_when_enabled(self):
        # GIVEN a previous step result and context enabled
        prev = make_step_run("step1", "Output from step1")
        step = LlmStep(id="s2", prompt="Do something")

        # WHEN building the prompt with context enabled
        result = self.builder.build(
            step=step,
            input_text="input",
            previous_results=[prev],
            include_previous_context=True,
        )

        # THEN the context section is appended
        self.assertIn("Do something", result)
        self.assertIn("Context from previous steps", result)
        self.assertIn("## step1", result)
        self.assertIn("Output from step1", result)

    def test_no_context_when_disabled(self):
        # GIVEN a previous step result but context disabled
        prev = make_step_run("step1", "Output from step1")
        step = LlmStep(id="s2", prompt="Do something")

        # WHEN building the prompt with context disabled
        result = self.builder.build(
            step=step,
            input_text="input",
            previous_results=[prev],
            include_previous_context=False,
        )

        # THEN no context is appended
        self.assertEqual(result, "Do something")

    def test_no_context_for_first_step(self):
        # GIVEN no previous results (first step)
        step = LlmStep(id="s1", prompt="First step")

        # WHEN building with context enabled but no prior steps
        result = self.builder.build(
            step=step,
            input_text="input",
            previous_results=[],
            include_previous_context=True,
        )

        # THEN no context section is added
        self.assertEqual(result, "First step")

    def test_multiple_previous_outputs_all_included(self):
        # GIVEN multiple previous step results
        prev1 = make_step_run("impact", "Impact analysis done")
        prev2 = make_step_run("plan", "Plan created")
        step = LlmStep(id="implement", prompt="Now implement")

        # WHEN building the prompt
        result = self.builder.build(
            step=step,
            input_text="input",
            previous_results=[prev1, prev2],
            include_previous_context=True,
        )

        # THEN all previous outputs are included with separators
        self.assertIn("## impact", result)
        self.assertIn("Impact analysis done", result)
        self.assertIn("## plan", result)
        self.assertIn("Plan created", result)
