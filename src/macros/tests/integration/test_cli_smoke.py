import unittest
import json
from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from macros.cli import app
from macros.application.container import Container
from macros.infrastructure.runtime.utils.workspace import set_workspace
from macros.tests.fakes import FakeAgent


# =============================================================================
# Test Macro Fixture
# =============================================================================

TEST_MACRO = {
    "macro_id": "test_flow",
    "name": "Test Flow",
    "engine": "cursor",
    "include_previous_outputs": True,
    "steps": [
        # Step 1: Tests {{INPUT}} substitution
        {"id": "analyze", "type": "llm", "prompt": "Analyze: {{INPUT}}"},
        # Step 2: Tests context accumulation (previous output appended)
        {"id": "plan", "type": "llm", "prompt": "Create plan based on analysis."},
        # Step 3: Gate after LLM steps
        {"id": "approve", "type": "gate", "message": "Approve plan?"},
        # Step 4: LLM after gate, explicit {{STEP_OUTPUT:id}} reference
        {"id": "implement", "type": "llm", "prompt": "Implement: {{STEP_OUTPUT:plan}}"},
        # Step 5: Multiple gates in flow
        {"id": "review", "type": "gate", "message": "Review complete?"},
        # Step 6: Reference non-adjacent step
        {"id": "finalize", "type": "llm", "prompt": "Finalize. Original was: {{STEP_OUTPUT:analyze}}"},
    ]
}


def write_test_macro(workspace: Path) -> None:
    """Write the test macro to the workspace."""
    macro_dir = workspace / ".macrocycle" / "macros"
    macro_dir.mkdir(parents=True, exist_ok=True)
    (macro_dir / "test_flow.json").write_text(json.dumps(TEST_MACRO))


# =============================================================================
# Tests
# =============================================================================

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
            Path(".git").mkdir()
            set_workspace(Path.cwd())

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
            Path(".git").mkdir()
            set_workspace(Path.cwd())

            # Create a container factory that injects fake agent
            def make_test_container():
                container = Container()
                container.agent = FakeAgent(text="Test output")
                return container

            self.runner.invoke(app, ["init"])

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

    def test_dry_run_shows_all_steps_with_correct_types(self):
        # GIVEN a workspace with test macro
        with self.runner.isolated_filesystem():
            Path(".git").mkdir()
            set_workspace(Path.cwd())
            write_test_macro(Path.cwd())
            # Also init cycles dir
            (Path.cwd() / ".macrocycle" / "cycles").mkdir(parents=True, exist_ok=True)

            # WHEN running with --dry-run
            result = self.runner.invoke(app, [
                "run", "test_flow", "My test input", "--dry-run"
            ])

            # THEN it succeeds
            self.assertEqual(result.exit_code, 0, msg=result.output)
            output = result.output

            # AND all 6 steps appear in preview
            self.assertIn("analyze", output)
            self.assertIn("plan", output)
            self.assertIn("approve", output)
            self.assertIn("implement", output)
            self.assertIn("review", output)
            self.assertIn("finalize", output)

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
        # GIVEN a workspace with test macro
        with self.runner.isolated_filesystem():
            Path(".git").mkdir()
            set_workspace(Path.cwd())
            write_test_macro(Path.cwd())
            (Path.cwd() / ".macrocycle" / "cycles").mkdir(parents=True, exist_ok=True)

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
        # GIVEN a workspace with test macro and auto-increment agent
        with self.runner.isolated_filesystem():
            Path(".git").mkdir()
            set_workspace(Path.cwd())
            write_test_macro(Path.cwd())
            (Path.cwd() / ".macrocycle" / "cycles").mkdir(parents=True, exist_ok=True)

            # Track the agent to inspect prompts
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
            prompt_1 = test_agent.prompts[0]
            self.assertIn("My test input", prompt_1)

            # AND prompt to step 2 contains output from step 1 (context accumulation)
            prompt_2 = test_agent.prompts[1]
            self.assertIn("Output from step 1", prompt_2)

            # AND prompt to step 4 (implement) contains output from plan via explicit reference
            # Note: Step 4 is the 3rd LLM call (after analyze, plan, then implement)
            prompt_4 = test_agent.prompts[2]
            self.assertIn("Output from step 2", prompt_4)  # {{STEP_OUTPUT:plan}}

            # AND prompt to step 6 (finalize) contains output from analyze (non-adjacent)
            prompt_6 = test_agent.prompts[3]
            self.assertIn("Output from step 1", prompt_6)  # {{STEP_OUTPUT:analyze}}

            # AND all expected artifacts were created
            cycles_dir = Path(".macrocycle/cycles")
            cycle_dirs = list(cycles_dir.iterdir())
            self.assertEqual(len(cycle_dirs), 1)

            cycle_dir = cycle_dirs[0]
            steps_dir = cycle_dir / "steps"
            
            # LLM steps create artifacts, gates don't
            self.assertTrue((steps_dir / "01-analyze.md").exists())
            self.assertTrue((steps_dir / "02-plan.md").exists())
            # Step 3 is gate - no artifact
            self.assertTrue((steps_dir / "04-implement.md").exists())
            # Step 5 is gate - no artifact
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
        # GIVEN a workspace with test macro
        with self.runner.isolated_filesystem():
            Path(".git").mkdir()
            set_workspace(Path.cwd())
            write_test_macro(Path.cwd())
            (Path.cwd() / ".macrocycle" / "cycles").mkdir(parents=True, exist_ok=True)

            test_agent = FakeAgent(auto_increment=True)

            def make_test_container():
                container = Container()
                container.agent = test_agent
                return container

            # WHEN running and denying at the gate (no --yes flag, simulate 'n')
            with patch("macros.cli.Container", make_test_container):
                result = self.runner.invoke(app, [
                    "run", "test_flow", "My test input"
                ], input="n\n")  # Deny at first gate

            # THEN only steps before gate executed (2 LLM steps)
            self.assertEqual(test_agent.call_count, 2)

            # AND cycle artifacts exist for steps 1-2 only
            cycles_dir = Path(".macrocycle/cycles")
            cycle_dirs = list(cycles_dir.iterdir())
            self.assertEqual(len(cycle_dirs), 1)

            cycle_dir = cycle_dirs[0]
            steps_dir = cycle_dir / "steps"
            
            self.assertTrue((steps_dir / "01-analyze.md").exists())
            self.assertTrue((steps_dir / "02-plan.md").exists())
            self.assertFalse((steps_dir / "04-implement.md").exists())
            self.assertFalse((steps_dir / "06-finalize.md").exists())

            # AND output indicates cancellation
            self.assertIn("stopped", result.output.lower())
