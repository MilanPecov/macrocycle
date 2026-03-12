"""Integration tests for the CLI."""

import unittest
from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from macros.cli import app
from macros.application.container import Container
from macros.infrastructure.runtime.utils.workspace import set_workspace
from macros.tests.helpers import (
    FakeAgent,
    FakeCommand,
    init_test_workspace,
    write_workflow_to_workspace,
    init_runs_dir,
    SAMPLE_WORKFLOW_DICT,
)


class TestCliInit(unittest.TestCase):

    def setUp(self):
        self.runner = CliRunner()

    def tearDown(self):
        set_workspace(None)

    def test_init_creates_directory_structure(self):
        with self.runner.isolated_filesystem():
            init_test_workspace(Path.cwd())
            result = self.runner.invoke(app, ["init"])

            self.assertEqual(result.exit_code, 0, msg=result.output)
            self.assertTrue(Path(".macrocycle/workflows").is_dir())
            self.assertTrue(Path(".macrocycle/runs").is_dir())
            self.assertTrue(Path(".macrocycle/workflows/fix.json").exists())


class TestCliRun(unittest.TestCase):

    def setUp(self):
        self.runner = CliRunner()

    def tearDown(self):
        set_workspace(None)

    def test_run_executes_workflow_and_creates_artifacts(self):
        with self.runner.isolated_filesystem():
            init_test_workspace(Path.cwd())
            write_workflow_to_workspace(Path.cwd(), SAMPLE_WORKFLOW_DICT)
            init_runs_dir(Path.cwd())

            def make_test_container():
                container = Container()
                container.command = FakeCommand(exit_code=0, output="passed")
                return container

            with patch("macros.cli.Container", make_test_container):
                with patch.object(
                    FakeAgent, "run_prompt", return_value=(0, "test output")
                ):
                    result = self.runner.invoke(app, [
                        "run", "sample", "Test input", "--until", "analyze"
                    ])

            self.assertEqual(result.exit_code, 0, msg=result.output)
            self.assertIn("Done", result.output)

    def test_run_missing_workflow_exits_with_error(self):
        with self.runner.isolated_filesystem():
            init_test_workspace(Path.cwd())
            init_runs_dir(Path.cwd())

            result = self.runner.invoke(app, ["run", "nonexistent", "input"])

            self.assertNotEqual(result.exit_code, 0)

    def test_run_without_input_exits_with_error(self):
        with self.runner.isolated_filesystem():
            init_test_workspace(Path.cwd())

            result = self.runner.invoke(app, ["run", "fix"])

            self.assertEqual(result.exit_code, 2)


class TestCliList(unittest.TestCase):

    def setUp(self):
        self.runner = CliRunner()

    def tearDown(self):
        set_workspace(None)

    def test_list_empty_workspace_exits_with_error(self):
        with self.runner.isolated_filesystem():
            init_test_workspace(Path.cwd())
            result = self.runner.invoke(app, ["list"])

            self.assertNotEqual(result.exit_code, 0)

    def test_list_shows_workflows(self):
        with self.runner.isolated_filesystem():
            init_test_workspace(Path.cwd())
            write_workflow_to_workspace(Path.cwd(), SAMPLE_WORKFLOW_DICT)

            result = self.runner.invoke(app, ["list"])

            self.assertEqual(result.exit_code, 0)
            self.assertIn("sample", result.output)
