"""Tests for FileWorkflowStore -- workflow persistence."""

import unittest
import tempfile
from pathlib import Path

from macros.domain.exceptions import WorkflowNotFoundError
from macros.infrastructure.persistence.workflow_store import FileWorkflowStore
from macros.infrastructure.runtime.utils.workspace import set_workspace
from macros.tests.helpers import init_test_workspace, write_workflow_to_workspace, SAMPLE_WORKFLOW_DICT


class TestFileWorkflowStore(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.workspace = Path(self.tmp.name)
        init_test_workspace(self.workspace)
        self.store = FileWorkflowStore()

    def tearDown(self):
        set_workspace(None)
        self.tmp.cleanup()

    def test_load_nonexistent_raises_not_found(self):
        with self.assertRaises(WorkflowNotFoundError):
            self.store.load_workflow("does_not_exist")

    def test_load_workflow_from_local(self):
        write_workflow_to_workspace(self.workspace, SAMPLE_WORKFLOW_DICT)
        wf = self.store.load_workflow("sample")

        self.assertEqual(wf.id, "sample")
        self.assertEqual(wf.name, "Sample Workflow")
        self.assertEqual(len(wf.phases), 2)

    def test_phases_parsed_correctly(self):
        write_workflow_to_workspace(self.workspace, SAMPLE_WORKFLOW_DICT)
        wf = self.store.load_workflow("sample")

        analyze = wf.phases[0]
        self.assertEqual(analyze.id, "analyze")
        self.assertEqual(analyze.on_complete, "implement")
        self.assertEqual(len(analyze.steps), 1)

        implement = wf.phases[1]
        self.assertEqual(implement.id, "implement")
        self.assertEqual(implement.max_iterations, 3)
        self.assertIsNotNone(implement.validation)
        self.assertEqual(implement.validation.command, "pytest -q")
        self.assertEqual(implement.context, ("analyze",))
        self.assertEqual(len(implement.steps), 2)

    def test_list_workflows_empty(self):
        result = self.store.list_workflows()
        self.assertEqual(result, [])

    def test_list_workflows_sorted(self):
        for name in ["zebra", "alpha", "beta"]:
            wf = {"id": name, "name": name, "agent": {"engine": "cursor"}, "phases": [
                {"id": "p", "steps": [{"id": "s", "type": "llm", "prompt": "x"}]}
            ]}
            write_workflow_to_workspace(self.workspace, wf)

        result = self.store.list_workflows()
        self.assertEqual(result, ["alpha", "beta", "zebra"])

    def test_init_default_workflows_creates_fix(self):
        self.store.init_default_workflows()

        wf = self.store.load_workflow("fix")
        self.assertEqual(wf.id, "fix")
        self.assertTrue(len(wf.phases) > 0)

    def test_init_default_does_not_overwrite_existing(self):
        custom = {"id": "fix", "name": "My Custom Fix", "agent": {"engine": "cursor"},
                  "phases": [{"id": "p", "steps": [{"id": "s", "type": "llm", "prompt": "x"}]}]}
        write_workflow_to_workspace(self.workspace, custom)

        self.store.init_default_workflows()

        wf = self.store.load_workflow("fix")
        self.assertEqual(wf.name, "My Custom Fix")

    def test_command_step_parsed(self):
        write_workflow_to_workspace(self.workspace, SAMPLE_WORKFLOW_DICT)
        wf = self.store.load_workflow("sample")

        from macros.domain.model.step import CommandStep
        implement = wf.phases[1]
        cmd_steps = [s for s in implement.steps if isinstance(s, CommandStep)]
        self.assertEqual(len(cmd_steps), 1)
        self.assertEqual(cmd_steps[0].command, "pytest -q")
