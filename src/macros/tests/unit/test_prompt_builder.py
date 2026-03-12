"""Tests for PromptBuilder -- variable substitution and feedback injection."""

import unittest
from types import MappingProxyType

from macros.domain.model.context import ExecutionContext
from macros.domain.services.prompt_builder import PromptBuilder
from macros.tests.helpers import make_step_run


class TestPromptBuilder(unittest.TestCase):

    def setUp(self):
        self.builder = PromptBuilder()

    def _ctx(self, **kwargs) -> ExecutionContext:
        defaults = {
            "input": "test input",
            "phase_outputs": MappingProxyType({}),
            "iteration": 1,
            "validation_output": None,
        }
        defaults.update(kwargs)
        return ExecutionContext(**defaults)

    def test_substitutes_input_variable(self):
        result = self.builder.build(
            "Analyze: {{INPUT}}",
            self._ctx(input="the bug"),
            [],
        )
        self.assertEqual(result, "Analyze: the bug")

    def test_substitutes_phase_output_variable(self):
        ctx = self._ctx(phase_outputs=MappingProxyType({"analyze": "analysis done"}))
        result = self.builder.build(
            "Based on: {{PHASE_OUTPUT:analyze}}",
            ctx,
            [],
        )
        self.assertEqual(result, "Based on: analysis done")

    def test_substitutes_step_output_variable(self):
        prev = make_step_run("impact", "impact result")
        result = self.builder.build(
            "Using: {{STEP_OUTPUT:impact}}",
            self._ctx(),
            [prev],
        )
        self.assertEqual(result, "Using: impact result")

    def test_substitutes_iteration_variable(self):
        ctx = self._ctx(iteration=3)
        result = self.builder.build("Attempt {{ITERATION}}", ctx, [])
        self.assertEqual(result, "Attempt 3")

    def test_substitutes_validation_output_variable(self):
        ctx = self._ctx(iteration=2, validation_output="FAILED: 3 tests")
        result = self.builder.build(
            "Errors: {{VALIDATION_OUTPUT}}",
            ctx,
            [],
        )
        self.assertIn("Errors: FAILED: 3 tests", result)

    def test_unknown_variables_kept_as_is(self):
        result = self.builder.build("{{UNKNOWN}} and {{INPUT}}", self._ctx(), [])
        self.assertEqual(result, "{{UNKNOWN}} and test input")

    def test_feedback_appended_on_iteration_gt_1(self):
        ctx = self._ctx(iteration=2, validation_output="2 tests failed")
        result = self.builder.build(
            "Fix the code",
            ctx,
            [],
            max_iterations=5,
        )
        self.assertIn("Validation Failed (attempt 2/5)", result)
        self.assertIn("2 tests failed", result)
        self.assertIn("Fix the issues above", result)

    def test_no_feedback_on_first_iteration(self):
        ctx = self._ctx(iteration=1, validation_output=None)
        result = self.builder.build("Fix the code", ctx, [])
        self.assertNotIn("Validation Failed", result)

    def test_no_feedback_when_validation_output_is_none(self):
        ctx = self._ctx(iteration=3, validation_output=None)
        result = self.builder.build("Fix the code", ctx, [])
        self.assertNotIn("Validation Failed", result)
