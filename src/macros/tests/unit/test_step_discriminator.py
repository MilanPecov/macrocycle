"""Tests for Step discriminated union parsing via MacroJsonMapper.

Critical invariant: The 'type' field determines which Step subclass is created.
This is essential for the orchestrator to handle steps correctly.
"""

import unittest

from macros.domain.model.macro import LlmStep, GateStep
from macros.infrastructure.persistence.mappers import MacroJsonMapper


class TestStepDiscriminator(unittest.TestCase):
    """Tests for Step type discrimination during JSON parsing."""

    def test_type_llm_creates_llm_step(self):
        # GIVEN JSON with type="llm"
        macro = MacroJsonMapper.from_dict({
            "macro_id": "test",
            "name": "Test",
            "steps": [{"id": "s1", "type": "llm", "prompt": "Do something"}]
        })

        # THEN an LlmStep is created
        self.assertIsInstance(macro.steps[0], LlmStep)
        self.assertEqual(macro.steps[0].prompt, "Do something")

    def test_type_gate_creates_gate_step(self):
        # GIVEN JSON with type="gate"
        macro = MacroJsonMapper.from_dict({
            "macro_id": "test",
            "name": "Test",
            "steps": [{"id": "g1", "type": "gate", "message": "Continue?"}]
        })

        # THEN a GateStep is created
        self.assertIsInstance(macro.steps[0], GateStep)
        self.assertEqual(macro.steps[0].message, "Continue?")

    def test_mixed_step_types_parsed_correctly(self):
        # GIVEN JSON with mixed step types
        macro = MacroJsonMapper.from_dict({
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

    def test_unknown_step_type_defaults_to_llm(self):
        # GIVEN JSON with unknown type but has prompt field
        # WHEN parsing
        # THEN it defaults to LlmStep (graceful handling)
        macro = MacroJsonMapper.from_dict({
            "macro_id": "test",
            "name": "Test",
            "steps": [{"id": "s1", "type": "unknown", "prompt": "X"}]
        })
        self.assertIsInstance(macro.steps[0], LlmStep)

    def test_llm_step_missing_prompt_raises_key_error(self):
        # GIVEN an LLM step without prompt
        # WHEN parsing
        # THEN KeyError is raised
        with self.assertRaises(KeyError):
            MacroJsonMapper.from_dict({
                "macro_id": "test",
                "name": "Test",
                "steps": [{"id": "s1", "type": "llm"}]  # missing prompt
            })

    def test_gate_step_has_default_message(self):
        # GIVEN a gate step without message
        macro = MacroJsonMapper.from_dict({
            "macro_id": "test",
            "name": "Test",
            "steps": [{"id": "g1", "type": "gate"}]  # no message
        })

        # THEN default message is used
        self.assertEqual(macro.steps[0].message, "Continue?")
