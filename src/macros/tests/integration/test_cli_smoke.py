import unittest
from pathlib import Path

from typer.testing import CliRunner

from macros.cli import app
from macros.application.container import Container
from macros.domain.ports.agent_port import AgentPort
from macros.infrastructure.runtime.workspace import set_workspace
import macros.cli as cli_module


class FakeAgent(AgentPort):
    """Test double that returns canned responses."""

    def __init__(self, text: str = "Hello from FakeAgent"):
        self.text = text
        self.calls: list[str] = []

    def run_prompt(self, prompt: str) -> tuple[int, str]:
        self.calls.append(prompt)
        return 0, self.text


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
            cli_module.container = Container()

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

            container = Container()
            container.agent = FakeAgent(text="Test output")
            cli_module.container = container

            self.runner.invoke(app, ["init"])

            # WHEN running a macro with --until to limit execution
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
