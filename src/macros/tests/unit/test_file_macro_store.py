import unittest
import tempfile
import json
from pathlib import Path

from macros.infrastructure.persistence import FileMacroStore
from macros.infrastructure.runtime.utils.workspace import set_workspace
from macros.domain.exceptions import MacroNotFoundError
from macros.tests.helpers import write_macro_to_workspace


class TestFileMacroStore(unittest.TestCase):
    """Tests for FileMacroStore - the macro persistence layer.
    
    Key invariants:
    - Unknown macro IDs raise MacroNotFoundError
    - Local macros take precedence over packaged defaults
    - list_macros returns empty when no macros exist
    """

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.workspace = Path(self.tmp.name)
        set_workspace(self.workspace)
        self.store = FileMacroStore()

    def tearDown(self):
        set_workspace(None)
        self.tmp.cleanup()

    # -------------------------------------------------------------------------
    # Loading Macros
    # -------------------------------------------------------------------------

    def test_load_nonexistent_macro_raises_macro_not_found(self):
        # GIVEN an empty workspace with no macros
        # WHEN loading a macro that doesn't exist
        # THEN MacroNotFoundError is raised
        with self.assertRaises(MacroNotFoundError) as ctx:
            self.store.load_macro("does_not_exist")
        
        self.assertIn("does_not_exist", str(ctx.exception))

    def test_local_macro_takes_precedence_over_packaged_default(self):
        # GIVEN a packaged default "fix" macro exists
        # AND a local "fix" macro with custom name
        custom_fix = {
            "macro_id": "fix",
            "name": "My Custom Fix",
            "engine": "cursor",
            "steps": [{"id": "s1", "type": "llm", "prompt": "Custom"}]
        }
        write_macro_to_workspace(self.workspace, custom_fix)

        # WHEN loading the "fix" macro
        macro = self.store.load_macro("fix")

        # THEN the local version is returned
        self.assertEqual(macro.name, "My Custom Fix")

    # -------------------------------------------------------------------------
    # Listing Macros
    # -------------------------------------------------------------------------

    def test_list_macros_returns_empty_when_no_directory(self):
        # GIVEN a workspace without .macrocycle/macros/
        # WHEN listing macros
        result = self.store.list_macros()

        # THEN empty list is returned
        self.assertEqual(result, [])

    def test_list_macros_returns_sorted_ids(self):
        # GIVEN multiple local macros
        for name in ["zebra", "alpha", "beta"]:
            macro = {"macro_id": name, "name": name, "steps": [{"id": "s", "type": "llm", "prompt": "x"}]}
            write_macro_to_workspace(self.workspace, macro)

        # WHEN listing macros
        result = self.store.list_macros()

        # THEN they are returned in sorted order
        self.assertEqual(result, ["alpha", "beta", "zebra"])

    # -------------------------------------------------------------------------
    # Initialization
    # -------------------------------------------------------------------------

    def test_init_default_macros_does_not_overwrite_existing(self):
        # GIVEN a local "fix" macro already exists
        existing_fix = {
            "macro_id": "fix",
            "name": "Already Here",
            "engine": "cursor",
            "steps": [{"id": "s1", "type": "llm", "prompt": "X"}]
        }
        write_macro_to_workspace(self.workspace, existing_fix)

        # WHEN initializing default macros
        self.store.init_default_macros()

        # THEN the existing file is NOT overwritten
        macro = self.store.load_macro("fix")
        self.assertEqual(macro.name, "Already Here")
