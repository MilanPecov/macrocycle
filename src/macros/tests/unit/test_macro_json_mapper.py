import unittest
import json
import tempfile

from macros.infrastructure.persistence import MacroJsonMapper, FileMacroStore
from macros.infrastructure.runtime.utils.workspace import set_workspace


class TestMacroJsonMapper(unittest.TestCase):
    """Tests for JSON serialization/deserialization of Macro definitions."""

    def tearDown(self):
        set_workspace(None)

    def test_packaged_default_macro_loads_correctly(self):
        # GIVEN the packaged default "fix" macro
        with tempfile.TemporaryDirectory() as tmp:
            set_workspace(tmp)
            store = FileMacroStore()

            # WHEN loading it via the mapper
            txt = store._load_packaged_default_text("fix")
            macro = MacroJsonMapper.from_json(txt)

            # THEN all required fields are present and valid
            self.assertEqual(macro.macro_id, "fix")
            self.assertEqual(macro.name, "Fix")
            self.assertTrue(macro.include_previous_outputs)
            self.assertGreater(len(macro.steps), 0)

    def test_json_round_trip_preserves_data(self):
        # GIVEN a macro loaded from JSON
        with tempfile.TemporaryDirectory() as tmp:
            set_workspace(tmp)
            store = FileMacroStore()
            original_text = store._load_packaged_default_text("fix")
            macro = MacroJsonMapper.from_json(original_text)

            # WHEN serializing back to JSON
            dumped = MacroJsonMapper.to_json(macro)
            parsed = json.loads(dumped)

            # THEN key fields are preserved
            self.assertEqual(parsed["macro_id"], "fix")
            self.assertEqual(parsed["engine"], "cursor")
            self.assertIn("steps", parsed)
