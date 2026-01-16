import unittest
import tempfile
import json
from pathlib import Path

from macros.infrastructure.persistence import FileMacroStore
from macros.infrastructure.runtime.utils.workspace import set_workspace


class TestFileMacroStore(unittest.TestCase):
    """Tests for FileMacroStore - the macro persistence layer.
    
    Key invariants:
    - Unknown macro IDs raise FileNotFoundError
    - Local macros take precedence over packaged defaults
    - list_macros returns empty when no macros exist
    """

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        set_workspace(self.tmp.name)
        self.store = FileMacroStore()

    def tearDown(self):
        set_workspace(None)
        self.tmp.cleanup()

    def test_load_nonexistent_macro_raises_file_not_found(self):
        # GIVEN an empty workspace with no macros
        # WHEN loading a macro that doesn't exist
        # THEN FileNotFoundError is raised
        with self.assertRaises(FileNotFoundError) as ctx:
            self.store.load_macro("does_not_exist")
        
        self.assertIn("does_not_exist", str(ctx.exception))

    def test_list_macros_returns_empty_when_no_directory(self):
        # GIVEN a workspace without .macrocycle/macros/
        # WHEN listing macros
        result = self.store.list_macros()

        # THEN empty list is returned
        self.assertEqual(result, [])

    def test_local_macro_takes_precedence_over_packaged_default(self):
        # GIVEN a packaged default "fix" macro exists
        # AND a local "fix" macro with custom name
        macro_dir = Path(self.tmp.name) / ".macrocycle" / "macros"
        macro_dir.mkdir(parents=True)
        
        custom_macro = {
            "macro_id": "fix",
            "name": "My Custom Fix",  # Different from packaged
            "engine": "cursor",
            "steps": [{"id": "s1", "type": "llm", "prompt": "Custom"}]
        }
        (macro_dir / "fix.json").write_text(json.dumps(custom_macro))

        # WHEN loading the "fix" macro
        macro = self.store.load_macro("fix")

        # THEN the local version is returned
        self.assertEqual(macro.name, "My Custom Fix")

    def test_init_default_macros_does_not_overwrite_existing(self):
        # GIVEN a local "fix" macro already exists
        macro_dir = Path(self.tmp.name) / ".macrocycle" / "macros"
        macro_dir.mkdir(parents=True)
        
        custom_content = json.dumps({
            "macro_id": "fix",
            "name": "Already Here",
            "engine": "cursor",
            "steps": [{"id": "s1", "type": "llm", "prompt": "X"}]
        })
        (macro_dir / "fix.json").write_text(custom_content)

        # WHEN initializing default macros
        self.store.init_default_macros()

        # THEN the existing file is NOT overwritten
        macro = self.store.load_macro("fix")
        self.assertEqual(macro.name, "Already Here")

    def test_list_macros_returns_sorted_ids(self):
        # GIVEN multiple local macros
        macro_dir = Path(self.tmp.name) / ".macrocycle" / "macros"
        macro_dir.mkdir(parents=True)
        
        for name in ["zebra", "alpha", "beta"]:
            macro = {"macro_id": name, "name": name, "steps": [{"id": "s", "type": "llm", "prompt": "x"}]}
            (macro_dir / f"{name}.json").write_text(json.dumps(macro))

        # WHEN listing macros
        result = self.store.list_macros()

        # THEN they are returned in sorted order
        self.assertEqual(result, ["alpha", "beta", "zebra"])
