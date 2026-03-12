"""Tests for PhaseExecutor -- the inner feedback control loop."""

import unittest
from types import MappingProxyType

from macros.domain.model.agent_config import AgentConfig
from macros.domain.model.context import ExecutionContext
from macros.domain.model.step import CommandStep, LlmStep
from macros.domain.model.workflow import Phase, Validation
from macros.domain.services.phase_executor import PhaseExecutor
from macros.domain.services.prompt_builder import PromptBuilder
from macros.tests.helpers import FakeAgent, FakeCommand, FakeConsole, make_phase


class TestPhaseExecutor(unittest.TestCase):

    def _make_executor(
        self, agent: FakeAgent | None = None, command: FakeCommand | None = None
    ) -> PhaseExecutor:
        agent = agent or FakeAgent()
        command = command or FakeCommand()
        self._agent = agent
        self._command = command

        def factory(config: AgentConfig) -> FakeAgent:
            return agent

        return PhaseExecutor(
            agent_factory=factory,
            command=command,
            prompt_builder=PromptBuilder(),
            console=FakeConsole(),
        )

    def _ctx(self, input_text: str = "test input") -> ExecutionContext:
        return ExecutionContext(input=input_text)

    def test_single_step_no_validation_converges_immediately(self):
        executor = self._make_executor(FakeAgent(text="done"))
        phase = make_phase("p", steps=(LlmStep(id="s1", prompt="Do: {{INPUT}}"),))

        result = executor.execute(phase, self._ctx(), AgentConfig())

        self.assertEqual(result.outcome, "converged")
        self.assertEqual(result.iteration, 1)
        self.assertEqual(len(result.step_runs), 1)
        self.assertEqual(result.output, "done")

    def test_validation_passes_first_try_converges(self):
        executor = self._make_executor(
            FakeAgent(text="fixed"),
            FakeCommand(exit_code=0, output="all tests passed"),
        )
        phase = make_phase(
            "p",
            max_iterations=3,
            validation=Validation(command="pytest"),
        )

        result = executor.execute(phase, self._ctx(), AgentConfig())

        self.assertEqual(result.outcome, "converged")
        self.assertEqual(result.iteration, 1)
        self.assertEqual(self._command.call_count, 1)

    def test_validation_fails_then_succeeds_converges_on_second_iteration(self):
        executor = self._make_executor(
            FakeAgent(auto_increment=True),
            FakeCommand(responses=[
                (1, "FAILED: 2 tests"),
                (0, "all passed"),
            ]),
        )
        phase = make_phase(
            "p",
            max_iterations=5,
            validation=Validation(command="pytest"),
        )

        result = executor.execute(phase, self._ctx(), AgentConfig())

        self.assertEqual(result.outcome, "converged")
        self.assertEqual(result.iteration, 2)
        self.assertEqual(self._agent.call_count, 2)
        self.assertEqual(self._command.call_count, 2)

    def test_validation_never_passes_exhausts_budget(self):
        executor = self._make_executor(
            FakeAgent(auto_increment=True),
            FakeCommand(exit_code=1, output="FAILED"),
        )
        phase = make_phase(
            "p",
            max_iterations=3,
            validation=Validation(command="pytest"),
        )

        result = executor.execute(phase, self._ctx(), AgentConfig())

        self.assertEqual(result.outcome, "exhausted")
        self.assertEqual(result.iteration, 3)
        self.assertEqual(self._agent.call_count, 3)
        self.assertEqual(self._command.call_count, 3)

    def test_validation_output_injected_as_feedback(self):
        executor = self._make_executor(
            FakeAgent(auto_increment=True),
            FakeCommand(responses=[
                (1, "test_foo FAILED\nAssertionError"),
                (0, "passed"),
            ]),
        )
        phase = make_phase(
            "p",
            max_iterations=3,
            validation=Validation(command="pytest"),
        )

        result = executor.execute(phase, self._ctx(), AgentConfig())

        self.assertIn("AssertionError", self._agent.prompts[1])
        self.assertIn("Validation Failed", self._agent.prompts[1])

    def test_command_step_uses_command_port(self):
        cmd = FakeCommand(exit_code=0, output="command output")
        executor = self._make_executor(command=cmd)
        phase = make_phase(
            "p",
            steps=(CommandStep(id="run_tests", command="pytest -q"),),
        )

        result = executor.execute(phase, self._ctx(), AgentConfig())

        self.assertEqual(cmd.commands, ["pytest -q"])
        self.assertEqual(result.step_runs[0].output, "command output")
        self.assertEqual(result.step_runs[0].exit_code, 0)

    def test_mixed_steps_execute_in_order(self):
        agent = FakeAgent(text="code written")
        cmd = FakeCommand(exit_code=0, output="tests pass")
        executor = self._make_executor(agent, cmd)
        phase = make_phase(
            "p",
            steps=(
                LlmStep(id="write", prompt="Write code"),
                CommandStep(id="test", command="pytest"),
            ),
        )

        result = executor.execute(phase, self._ctx(), AgentConfig())

        self.assertEqual(len(result.step_runs), 2)
        self.assertEqual(result.step_runs[0].step_id, "write")
        self.assertEqual(result.step_runs[1].step_id, "test")

    def test_agent_config_cascade(self):
        """Step agent overrides phase agent overrides workflow agent."""
        agents_seen: list[AgentConfig] = []
        base_agent = FakeAgent(text="ok")

        def tracking_factory(config: AgentConfig) -> FakeAgent:
            agents_seen.append(config)
            return base_agent

        step_agent = AgentConfig(engine="codex", model="o3")
        phase_agent = AgentConfig(engine="claude")
        workflow_agent = AgentConfig(engine="cursor", model="default")

        executor = PhaseExecutor(
            agent_factory=tracking_factory,
            command=FakeCommand(),
            prompt_builder=PromptBuilder(),
            console=FakeConsole(),
        )
        phase = Phase(
            id="p",
            steps=(LlmStep(id="s1", prompt="x", agent=step_agent),),
            agent=phase_agent,
        )

        executor.execute(phase, self._ctx(), workflow_agent)

        self.assertEqual(agents_seen[0].engine, "codex")
        self.assertEqual(agents_seen[0].model, "o3")

    def test_step_runs_record_resolved_agent_config(self):
        executor = self._make_executor(FakeAgent(text="ok"))
        phase = make_phase("p")

        result = executor.execute(phase, self._ctx(), AgentConfig(engine="cursor"))

        self.assertIsNotNone(result.step_runs[0].agent_config)
        self.assertEqual(result.step_runs[0].agent_config.engine, "cursor")

    def test_phase_output_is_last_step_output(self):
        agent = FakeAgent(auto_increment=True)
        executor = self._make_executor(agent)
        phase = make_phase(
            "p",
            steps=(
                LlmStep(id="first", prompt="A"),
                LlmStep(id="second", prompt="B"),
            ),
        )

        result = executor.execute(phase, self._ctx(), AgentConfig())

        self.assertEqual(result.output, "Output from call 2")
