import unittest
import json
import tempfile
from pathlib import Path

from macros.infrastructure.persistence import MacroJsonMapper
from macros.infrastructure.runtime.utils.workspace import set_workspace


# Sample valid macro JSON for testing
SAMPLE_MACRO_JSON = json.dumps({
    "macro_id": "test",
    "name": "Test Macro",
    "engine": "cursor",
    "include_previous_outputs": True,
    "steps": [
        {"id": "s1", "type": "llm", "prompt": "Do something with {{INPUT}}"},
        {"id": "g1", "type": "gate", "message": "Continue?"},
        {"id": "s2", "type": "llm", "prompt": "Based on: {{STEP_OUTPUT:s1}}"},
    ]
})


class TestMacroJsonMapper(unittest.TestCase):
    """Tests for JSON serialization/deserialization of Macro definitions."""

    def test_from_json_parses_valid_macro(self):
        # GIVEN valid macro JSON
        # WHEN parsing
        macro = MacroJsonMapper.from_json(SAMPLE_MACRO_JSON)

        # THEN all fields are correctly populated
        self.assertEqual(macro.macro_id, "test")
        self.assertEqual(macro.name, "Test Macro")
        self.assertEqual(macro.engine, "cursor")
        self.assertTrue(macro.include_previous_outputs)
        self.assertEqual(len(macro.steps), 3)

    def test_json_round_trip_preserves_data(self):
        # GIVEN a macro loaded from JSON
        macro = MacroJsonMapper.from_json(SAMPLE_MACRO_JSON)

        # WHEN serializing back to JSON and parsing again
        dumped = MacroJsonMapper.to_json(macro)
        parsed = json.loads(dumped)

        # THEN key fields are preserved
        self.assertEqual(parsed["macro_id"], "test")
        self.assertEqual(parsed["engine"], "cursor")
        self.assertEqual(len(parsed["steps"]), 3)

    def test_to_dict_creates_serializable_dict(self):
        # GIVEN a macro
        macro = MacroJsonMapper.from_json(SAMPLE_MACRO_JSON)

        # WHEN converting to dict
        data = MacroJsonMapper.to_dict(macro)

        # THEN result is a plain dict
        self.assertIsInstance(data, dict)
        self.assertEqual(data["macro_id"], "test")

    def test_from_dict_parses_dict(self):
        # GIVEN macro data as dict
        data = json.loads(SAMPLE_MACRO_JSON)

        # WHEN parsing from dict
        macro = MacroJsonMapper.from_dict(data)

        # THEN macro is created correctly
        self.assertEqual(macro.macro_id, "test")
        self.assertEqual(len(macro.steps), 3)
