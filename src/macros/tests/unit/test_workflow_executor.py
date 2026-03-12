"""Tests for WorkflowExecutor -- the outer control loop."""

import unittest

from macros.domain.model.agent_config import AgentConfig
from macros.domain.model.run import RunStatus
from macros.domain.model.step import LlmStep
from macros.domain.model.workflow import Phase, Validation
from macros.domain.services.phase_executor import PhaseExecutor
from macros.domain.services.prompt_builder import PromptBuilder
from macros.domain.services.workflow_executor import WorkflowExecutor
from macros.tests.helpers import (
    FakeAgent,
    FakeCommand,
    FakeConsole,
    FakeRunStore,
    make_workflow,
    make_phase,
)


class TestWorkflowExecutor(unittest.TestCase):

    def _make_executor(
        self,
        agent: FakeAgent | None = None,
        command: FakeCommand | None = None,
        store: FakeRunStore | None = None,
    ) -> WorkflowExecutor:
        agent = agent or FakeAgent()
        command = command or FakeCommand()
        store = store or FakeRunStore()
        self._agent = agent
        self._command = command
        self._store = store
        self._console = FakeConsole()

        def factory(config: AgentConfig) -> FakeAgent:
            return agent

        phase_executor = PhaseExecutor(
            agent_factory=factory,
            command=command,
            prompt_builder=PromptBuilder(),
            console=self._console,
        )
        return WorkflowExecutor(
            phase_executor=phase_executor,
            store=store,
            console=self._console,
        )

    def test_single_phase_workflow_completes(self):
        executor = self._make_executor(FakeAgent(text="done"))
        wf = make_workflow(phases=(make_phase("only"),))

        run = executor.execute(wf, "test input")

        self.assertEqual(run.status, RunStatus.COMPLETED)
        self.assertEqual(len(run.phase_runs), 1)
        self.assertEqual(run.phase_runs[0].phase_id, "only")
        self.assertEqual(run.phase_runs[0].outcome, "converged")

    def test_multi_phase_sequencing(self):
        executor = self._make_executor(FakeAgent(auto_increment=True))
        wf = make_workflow(phases=(
            make_phase("a", on_complete="b"),
            make_phase("b", on_complete="c"),
            make_phase("c"),
        ))

        run = executor.execute(wf, "input")

        self.assertEqual(run.status, RunStatus.COMPLETED)
        self.assertEqual(len(run.phase_runs), 3)
        self.assertEqual([pr.phase_id for pr in run.phase_runs], ["a", "b", "c"])

    def test_context_filtering_passes_only_declared_deps(self):
        """Phase c declares context=["a"], so it should NOT see output from b."""
        prompts_seen: list[str] = []
        agent = FakeAgent(auto_increment=True)
        original_run_prompt = agent.run_prompt

        def tracking_run(prompt: str) -> tuple[int, str]:
            prompts_seen.append(prompt)
            return original_run_prompt(prompt)

        agent.run_prompt = tracking_run

        executor = self._make_executor(agent)
        wf = make_workflow(phases=(
            make_phase("a", on_complete="b",
                       steps=(LlmStep(id="s1", prompt="Do: {{INPUT}}"),)),
            make_phase("b", on_complete="c",
                       steps=(LlmStep(id="s2", prompt="Middle"),)),
            make_phase("c", context=("a",),
                       steps=(LlmStep(id="s3", prompt="Final: {{PHASE_OUTPUT:a}}"),)),
        ))

        run = executor.execute(wf, "hello")

        last_prompt = prompts_seen[-1]
        self.assertIn("Output from call 1", last_prompt)

    def test_stop_after_halts_at_specified_phase(self):
        executor = self._make_executor(FakeAgent(auto_increment=True))
        wf = make_workflow(phases=(
            make_phase("a", on_complete="b"),
            make_phase("b", on_complete="c"),
            make_phase("c"),
        ))

        run = executor.execute(wf, "input", stop_after="a")

        self.assertEqual(run.status, RunStatus.COMPLETED)
        self.assertEqual(len(run.phase_runs), 1)
        self.assertEqual(run.phase_runs[0].phase_id, "a")

    def test_max_phase_visits_prevents_infinite_loop(self):
        executor = self._make_executor(FakeAgent(text="loop"))
        wf = make_workflow(
            phases=(
                make_phase("a", on_complete="b"),
                make_phase("b", on_complete="a"),
            ),
        )
        wf = make_workflow(
            phases=(
                make_phase("a", on_complete="b"),
                make_phase("b", on_complete="a"),
            ),
        )
        from dataclasses import replace
        wf = replace(wf, max_phase_visits=5)

        run = executor.execute(wf, "input")

        self.assertEqual(run.status, RunStatus.FAILED)
        self.assertIn("max_phase_visits", run.failure_reason)
        self.assertLessEqual(len(run.phase_runs), 5)

    def test_exhausted_phase_routes_via_on_exhausted(self):
        executor = self._make_executor(
            FakeAgent(auto_increment=True),
            FakeCommand(exit_code=1, output="FAIL"),
        )
        wf = make_workflow(phases=(
            make_phase(
                "build",
                max_iterations=2,
                validation=Validation(command="pytest"),
                on_complete="ship",
                on_exhausted="fallback",
            ),
            make_phase("ship"),
            make_phase("fallback"),
        ))

        run = executor.execute(wf, "input")

        self.assertEqual(run.status, RunStatus.COMPLETED)
        self.assertEqual(run.phase_runs[0].phase_id, "build")
        self.assertEqual(run.phase_runs[0].outcome, "exhausted")
        self.assertEqual(run.phase_runs[1].phase_id, "fallback")

    def test_input_saved_as_artifact(self):
        store = FakeRunStore()
        executor = self._make_executor(store=store)
        wf = make_workflow()

        executor.execute(wf, "my important input")

        input_artifacts = [(d, r, c) for d, r, c in store.artifacts if r == "input.txt"]
        self.assertEqual(len(input_artifacts), 1)
        self.assertEqual(input_artifacts[0][2], "my important input")

    def test_manifest_saved_after_each_phase(self):
        store = FakeRunStore()
        executor = self._make_executor(store=store)
        wf = make_workflow(phases=(
            make_phase("a", on_complete="b"),
            make_phase("b"),
        ))

        executor.execute(wf, "input")

        self.assertGreaterEqual(len(store.manifests), 2)

    def test_phase_output_written_as_artifact(self):
        store = FakeRunStore()
        executor = self._make_executor(FakeAgent(text="result"), store=store)
        wf = make_workflow(phases=(make_phase("analyze"),))

        executor.execute(wf, "input")

        output_artifacts = [
            (d, r, c) for d, r, c in store.artifacts if "output.md" in r
        ]
        self.assertEqual(len(output_artifacts), 1)
        self.assertIn("result", output_artifacts[0][2])
