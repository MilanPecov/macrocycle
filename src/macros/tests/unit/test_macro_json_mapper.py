import unittest
import json

from macros.infrastructure.persistence import MacroJsonMapper
from macros.tests.helpers import SAMPLE_MACRO_JSON, SAMPLE_MACRO_DICT


class TestMacroJsonMapper(unittest.TestCase):
    """Tests for JSON serialization/deserialization of Macro definitions."""

    # -------------------------------------------------------------------------
    # Parsing
    # -------------------------------------------------------------------------

    def test_from_json_parses_valid_macro(self):
        # GIVEN valid macro JSON
        # WHEN parsing
        macro = MacroJsonMapper.from_json(SAMPLE_MACRO_JSON)

        # THEN all fields are correctly populated
        self.assertEqual(macro.macro_id, "sample")
        self.assertEqual(macro.name, "Sample Macro")
        self.assertEqual(macro.engine, "cursor")
        self.assertTrue(macro.include_previous_outputs)
        self.assertEqual(len(macro.steps), 3)

    def test_from_dict_parses_dict(self):
        # GIVEN macro data as dict
        # WHEN parsing from dict
        macro = MacroJsonMapper.from_dict(SAMPLE_MACRO_DICT)

        # THEN macro is created correctly
        self.assertEqual(macro.macro_id, "sample")
        self.assertEqual(len(macro.steps), 3)

    # -------------------------------------------------------------------------
    # Serialization
    # -------------------------------------------------------------------------

    def test_json_round_trip_preserves_data(self):
        # GIVEN a macro loaded from JSON
        macro = MacroJsonMapper.from_json(SAMPLE_MACRO_JSON)

        # WHEN serializing back to JSON and parsing again
        dumped = MacroJsonMapper.to_json(macro)
        parsed = json.loads(dumped)

        # THEN key fields are preserved
        self.assertEqual(parsed["macro_id"], "sample")
        self.assertEqual(parsed["engine"], "cursor")
        self.assertEqual(len(parsed["steps"]), 3)

    def test_to_dict_creates_serializable_dict(self):
        # GIVEN a macro
        macro = MacroJsonMapper.from_json(SAMPLE_MACRO_JSON)

        # WHEN converting to dict
        data = MacroJsonMapper.to_dict(macro)

        # THEN result is a plain dict
        self.assertIsInstance(data, dict)
        self.assertEqual(data["macro_id"], "sample")
