import unittest
from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from macros.cli import app
from macros.application.container import Container
from macros.infrastructure.runtime.utils.workspace import set_workspace
from macros.tests.helpers import (
    FakeAgent,
    E2E_TEST_MACRO,
    init_test_workspace,
    write_macro_to_workspace,
    init_cycles_dir,
)


class TestCliEndToEnd(unittest.TestCase):
    """Integration tests for the CLI.
    
    These tests verify the full flow from CLI invocation to file artifacts.
    """

    def setUp(self):
        self.runner = CliRunner()

    def tearDown(self):
        set_workspace(None)

    def test_init_creates_macrocycle_directory_structure(self):
        # GIVEN an empty git repository
        with self.runner.isolated_filesystem():
            init_test_workspace(Path.cwd())

            # WHEN running 'macrocycle init'
            result = self.runner.invoke(app, ["init"])

            # THEN it succeeds and creates the directory structure
            self.assertEqual(result.exit_code, 0, msg=result.output)
            self.assertTrue(Path(".macrocycle/macros").is_dir())
            self.assertTrue(Path(".macrocycle/cycles").is_dir())
            self.assertTrue(Path(".macrocycle/macros/fix.json").exists())

    def test_run_executes_macro_and_creates_artifacts(self):
        # GIVEN an initialized workspace with a fake agent
        with self.runner.isolated_filesystem():
            init_test_workspace(Path.cwd())
            self.runner.invoke(app, ["init"])

            def make_test_container():
                container = Container()
                container.agent = FakeAgent(text="Test output")
                return container

            # WHEN running a macro with --until to limit execution
            with patch("macros.cli.Container", make_test_container):
                result = self.runner.invoke(app, [
                    "run", "fix", "Test input", "--until", "impact"
                ])

            # THEN it succeeds
            self.assertEqual(result.exit_code, 0, msg=result.output)

            # AND creates cycle artifacts
            cycles_dir = Path(".macrocycle/cycles")
            cycle_dirs = list(cycles_dir.iterdir())
            self.assertEqual(len(cycle_dirs), 1)

            # AND writes the step output
            step_file = cycle_dirs[0] / "steps/01-impact.md"
            self.assertTrue(step_file.exists())
            self.assertEqual(step_file.read_text(), "Test output")


class TestDryRunPreview(unittest.TestCase):
    """Tests for --dry-run preview mode.
    
    Verifies that dry-run shows correct preview without executing.
    """

    def setUp(self):
        self.runner = CliRunner()

    def tearDown(self):
        set_workspace(None)

    def _setup_workspace_with_test_macro(self) -> None:
        """GIVEN a workspace with the E2E test macro."""
        init_test_workspace(Path.cwd())
        write_macro_to_workspace(Path.cwd(), E2E_TEST_MACRO)
        init_cycles_dir(Path.cwd())

    def test_dry_run_shows_all_steps_with_correct_types(self):
        with self.runner.isolated_filesystem():
            # GIVEN a workspace with test macro
            self._setup_workspace_with_test_macro()

            # WHEN running with --dry-run
            result = self.runner.invoke(app, [
                "run", "test_flow", "My test input", "--dry-run"
            ])

            # THEN it succeeds
            self.assertEqual(result.exit_code, 0, msg=result.output)
            output = result.output

            # AND all 6 steps appear in preview
            for step_id in ["analyze", "plan", "approve", "implement", "review", "finalize"]:
                self.assertIn(step_id, output)

            # AND step types are shown correctly
            self.assertIn("[llm]", output)
            self.assertIn("[gate]", output)

            # AND input text appears in step 1 (not {{INPUT}} literal)
            self.assertIn("My test input", output)
            self.assertNotIn("{{INPUT}}", output)

            # AND STEP_OUTPUT placeholders show correctly
            self.assertIn("[← output from: plan]", output)
            self.assertIn("[← output from: analyze]", output)

            # AND gate messages are displayed
            self.assertIn("Approve plan?", output)
            self.assertIn("Review complete?", output)

    def test_dry_run_does_not_create_artifacts(self):
        with self.runner.isolated_filesystem():
            # GIVEN a workspace with test macro
            self._setup_workspace_with_test_macro()

            # WHEN running with --dry-run
            result = self.runner.invoke(app, [
                "run", "test_flow", "My test input", "--dry-run"
            ])

            # THEN no cycle artifacts are created
            cycles_dir = Path(".macrocycle/cycles")
            cycle_dirs = list(cycles_dir.iterdir())
            self.assertEqual(len(cycle_dirs), 0, "Dry-run should not create cycle directories")


class TestFullFlowWithContextVerification(unittest.TestCase):
    """Tests for full macro execution with context accumulation.
    
    Verifies that prompts contain correct context from previous steps.
    """

    def setUp(self):
        self.runner = CliRunner()

    def tearDown(self):
        set_workspace(None)

    def test_full_flow_accumulates_context_correctly(self):
        with self.runner.isolated_filesystem():
            # GIVEN a workspace with test macro and auto-increment agent
            init_test_workspace(Path.cwd())
            write_macro_to_workspace(Path.cwd(), E2E_TEST_MACRO)
            init_cycles_dir(Path.cwd())

            test_agent = FakeAgent(auto_increment=True)

            def make_test_container():
                container = Container()
                container.agent = test_agent
                return container

            # WHEN running full macro with --yes to auto-approve gates
            with patch("macros.cli.Container", make_test_container):
                result = self.runner.invoke(app, [
                    "run", "test_flow", "My test input", "--yes"
                ])

            # THEN it succeeds
            self.assertEqual(result.exit_code, 0, msg=result.output)

            # AND agent was called 4 times (4 LLM steps, 2 gates skipped)
            self.assertEqual(test_agent.call_count, 4)

            # AND prompt to step 1 contains input text
            self.assertIn("My test input", test_agent.prompts[0])

            # AND prompt to step 2 contains output from step 1 (context accumulation)
            self.assertIn("Output from step 1", test_agent.prompts[1])

            # AND prompt to step 4 (implement) contains output from plan via explicit reference
            self.assertIn("Output from step 2", test_agent.prompts[2])

            # AND prompt to step 6 (finalize) contains output from analyze (non-adjacent)
            self.assertIn("Output from step 1", test_agent.prompts[3])

            # AND all expected artifacts were created
            cycles_dir = Path(".macrocycle/cycles")
            cycle_dirs = list(cycles_dir.iterdir())
            self.assertEqual(len(cycle_dirs), 1)

            steps_dir = cycle_dirs[0] / "steps"
            self.assertTrue((steps_dir / "01-analyze.md").exists())
            self.assertTrue((steps_dir / "02-plan.md").exists())
            self.assertTrue((steps_dir / "04-implement.md").exists())
            self.assertTrue((steps_dir / "06-finalize.md").exists())


class TestGateDenial(unittest.TestCase):
    """Tests for gate denial behavior.
    
    Verifies that denying a gate stops execution correctly.
    """

    def setUp(self):
        self.runner = CliRunner()

    def tearDown(self):
        set_workspace(None)

    def test_gate_denial_stops_execution(self):
        with self.runner.isolated_filesystem():
            # GIVEN a workspace with test macro
            init_test_workspace(Path.cwd())
            write_macro_to_workspace(Path.cwd(), E2E_TEST_MACRO)
            init_cycles_dir(Path.cwd())

            test_agent = FakeAgent(auto_increment=True)

            def make_test_container():
                container = Container()
                container.agent = test_agent
                return container

            # WHEN running and denying at the gate (no --yes flag, simulate 'n')
            with patch("macros.cli.Container", make_test_container):
                result = self.runner.invoke(app, [
                    "run", "test_flow", "My test input"
                ], input="n\n")

            # THEN only steps before gate executed (2 LLM steps)
            self.assertEqual(test_agent.call_count, 2)

            # AND cycle artifacts exist for steps 1-2 only
            cycles_dir = Path(".macrocycle/cycles")
            cycle_dirs = list(cycles_dir.iterdir())
            self.assertEqual(len(cycle_dirs), 1)

            steps_dir = cycle_dirs[0] / "steps"
            self.assertTrue((steps_dir / "01-analyze.md").exists())
            self.assertTrue((steps_dir / "02-plan.md").exists())
            self.assertFalse((steps_dir / "04-implement.md").exists())
            self.assertFalse((steps_dir / "06-finalize.md").exists())

            # AND output indicates cancellation
            self.assertIn("stopped", result.output.lower())
