import unittest

from macros.domain.model.macro import Macro, LlmStep, GateStep
from macros.domain.services.macro_validator import MacroValidator
from macros.domain.exceptions import MacroValidationError


class TestMacroValidator(unittest.TestCase):
    """Tests for MacroValidator domain validation rules.
    
    Validates:
    - At least one step required
    - Unique step IDs
    - Step output references must point to earlier steps
    """

    def setUp(self):
        self.validator = MacroValidator()

    def test_valid_macro_with_references_passes(self):
        # GIVEN a macro with valid step references and mixed step types
        macro = Macro(
            macro_id="valid",
            name="Valid Macro",
            steps=[
                LlmStep(id="analyze", prompt="Analyze: {{INPUT}}"),
                GateStep(id="approve", message="Continue?"),
                LlmStep(id="implement", prompt="Based on: {{STEP_OUTPUT:analyze}}"),
            ],
        )

        # WHEN validating
        # THEN no exception is raised
        self.validator.validate(macro)

    def test_empty_steps_rejected(self):
        # GIVEN a macro with no steps
        macro = Macro(macro_id="empty", name="Empty", steps=[])

        # WHEN validating
        # THEN MacroValidationError is raised
        with self.assertRaises(MacroValidationError) as ctx:
            self.validator.validate(macro)
        self.assertIn("at least one step", str(ctx.exception))

    def test_duplicate_step_ids_rejected(self):
        # GIVEN a macro with duplicate step IDs
        macro = Macro(
            macro_id="dup",
            name="Duplicate",
            steps=[
                LlmStep(id="same", prompt="A"),
                LlmStep(id="same", prompt="B"),
            ],
        )

        # WHEN validating
        # THEN MacroValidationError mentions the duplicate ID
        with self.assertRaises(MacroValidationError) as ctx:
            self.validator.validate(macro)
        self.assertIn("Duplicate step ID 'same'", str(ctx.exception))

    def test_forward_reference_rejected(self):
        # GIVEN a step that references a step defined later
        macro = Macro(
            macro_id="forward",
            name="Forward Ref",
            steps=[
                LlmStep(id="a", prompt="Use {{STEP_OUTPUT:b}}"),  # b is after a
                LlmStep(id="b", prompt="B"),
            ],
        )

        # WHEN validating
        # THEN MacroValidationError mentions the invalid reference
        with self.assertRaises(MacroValidationError) as ctx:
            self.validator.validate(macro)
        self.assertIn("references unknown or future step 'b'", str(ctx.exception))

    def test_nonexistent_reference_rejected(self):
        # GIVEN a step referencing a step that doesn't exist
        macro = Macro(
            macro_id="missing",
            name="Missing Ref",
            steps=[
                LlmStep(id="a", prompt="Use {{STEP_OUTPUT:nonexistent}}"),
            ],
        )

        # WHEN validating
        # THEN MacroValidationError mentions the missing step
        with self.assertRaises(MacroValidationError) as ctx:
            self.validator.validate(macro)
        self.assertIn("references unknown or future step 'nonexistent'", str(ctx.exception))
