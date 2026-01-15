import unittest

from pydantic import ValidationError

from macros.domain.model.macro import Macro, LlmStep, GateStep


class TestStepDiscriminator(unittest.TestCase):
    """Tests for Step discriminated union parsing.
    
    Critical invariant: The 'type' field determines which Step subclass is created.
    This is essential for the orchestrator to handle steps correctly.
    """

    def test_type_llm_creates_llm_step(self):
        # GIVEN JSON with type="llm"
        macro = Macro.model_validate({
            "macro_id": "test",
            "name": "Test",
            "steps": [{"id": "s1", "type": "llm", "prompt": "Do something"}]
        })

        # THEN an LlmStep is created
        self.assertIsInstance(macro.steps[0], LlmStep)
        self.assertEqual(macro.steps[0].prompt, "Do something")

    def test_type_gate_creates_gate_step(self):
        # GIVEN JSON with type="gate"
        macro = Macro.model_validate({
            "macro_id": "test",
            "name": "Test",
            "steps": [{"id": "g1", "type": "gate", "message": "Continue?"}]
        })

        # THEN a GateStep is created
        self.assertIsInstance(macro.steps[0], GateStep)
        self.assertEqual(macro.steps[0].message, "Continue?")

    def test_mixed_step_types_parsed_correctly(self):
        # GIVEN JSON with mixed step types
        macro = Macro.model_validate({
            "macro_id": "test",
            "name": "Test",
            "steps": [
                {"id": "s1", "type": "llm", "prompt": "First"},
                {"id": "g1", "type": "gate", "message": "Approve?"},
                {"id": "s2", "type": "llm", "prompt": "Second"},
            ]
        })

        # THEN each step has correct type
        self.assertIsInstance(macro.steps[0], LlmStep)
        self.assertIsInstance(macro.steps[1], GateStep)
        self.assertIsInstance(macro.steps[2], LlmStep)

    def test_unknown_step_type_raises_validation_error(self):
        # GIVEN JSON with invalid type
        # WHEN parsing
        # THEN ValidationError is raised
        with self.assertRaises(ValidationError):
            Macro.model_validate({
                "macro_id": "test",
                "name": "Test",
                "steps": [{"id": "s1", "type": "unknown", "prompt": "X"}]
            })

    def test_llm_step_requires_prompt(self):
        # GIVEN an LLM step without prompt
        # WHEN parsing
        # THEN ValidationError is raised
        with self.assertRaises(ValidationError):
            Macro.model_validate({
                "macro_id": "test",
                "name": "Test",
                "steps": [{"id": "s1", "type": "llm"}]  # missing prompt
            })

    def test_gate_step_has_default_message(self):
        # GIVEN a gate step without message
        macro = Macro.model_validate({
            "macro_id": "test",
            "name": "Test",
            "steps": [{"id": "g1", "type": "gate"}]  # no message
        })

        # THEN default message is used
        self.assertEqual(macro.steps[0].message, "Continue?")
