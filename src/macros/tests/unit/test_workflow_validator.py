"""Tests for WorkflowValidator -- definition-time invariant enforcement."""

import unittest

from macros.domain.exceptions import WorkflowValidationError
from macros.domain.model.step import LlmStep
from macros.domain.model.workflow import Phase, Validation
from macros.domain.services.workflow_validator import WorkflowValidator
from macros.tests.helpers import make_workflow, make_phase


class TestWorkflowValidator(unittest.TestCase):

    def setUp(self):
        self.validator = WorkflowValidator()

    def test_valid_workflow_passes(self):
        wf = make_workflow(phases=(
            make_phase("a", on_complete="b"),
            make_phase("b"),
        ))
        self.validator.validate(wf)

    def test_empty_phases_rejected(self):
        wf = make_workflow(phases=())
        with self.assertRaises(WorkflowValidationError) as ctx:
            self.validator.validate(wf)
        self.assertIn("at least one phase", str(ctx.exception))

    def test_duplicate_phase_ids_rejected(self):
        wf = make_workflow(phases=(
            make_phase("same"),
            make_phase("same"),
        ))
        with self.assertRaises(WorkflowValidationError) as ctx:
            self.validator.validate(wf)
        self.assertIn("Duplicate phase ID 'same'", str(ctx.exception))

    def test_duplicate_step_ids_within_phase_rejected(self):
        phase = make_phase(
            "p",
            steps=(
                LlmStep(id="dup", prompt="A"),
                LlmStep(id="dup", prompt="B"),
            ),
        )
        wf = make_workflow(phases=(phase,))
        with self.assertRaises(WorkflowValidationError) as ctx:
            self.validator.validate(wf)
        self.assertIn("Duplicate step ID 'dup'", str(ctx.exception))

    def test_on_complete_references_unknown_phase_rejected(self):
        wf = make_workflow(phases=(
            make_phase("a", on_complete="nonexistent"),
        ))
        with self.assertRaises(WorkflowValidationError) as ctx:
            self.validator.validate(wf)
        self.assertIn("unknown phase 'nonexistent'", str(ctx.exception))

    def test_on_exhausted_references_unknown_phase_rejected(self):
        wf = make_workflow(phases=(
            make_phase("a", on_exhausted="nonexistent"),
        ))
        with self.assertRaises(WorkflowValidationError) as ctx:
            self.validator.validate(wf)
        self.assertIn("unknown phase 'nonexistent'", str(ctx.exception))

    def test_context_references_unknown_phase_rejected(self):
        wf = make_workflow(phases=(
            make_phase("a", context=("nonexistent",)),
        ))
        with self.assertRaises(WorkflowValidationError) as ctx:
            self.validator.validate(wf)
        self.assertIn("does not exist", str(ctx.exception))

    def test_max_iterations_zero_rejected(self):
        phase = make_phase("a", max_iterations=0)
        wf = make_workflow(phases=(phase,))
        with self.assertRaises(WorkflowValidationError) as ctx:
            self.validator.validate(wf)
        self.assertIn("max_iterations must be >= 1", str(ctx.exception))

    def test_valid_context_references_pass(self):
        wf = make_workflow(phases=(
            make_phase("a", on_complete="b"),
            make_phase("b", context=("a",)),
        ))
        self.validator.validate(wf)

    def test_validation_phase_with_iterations(self):
        phase = make_phase(
            "build",
            max_iterations=5,
            validation=Validation(command="pytest -q"),
        )
        wf = make_workflow(phases=(phase,))
        self.validator.validate(wf)
