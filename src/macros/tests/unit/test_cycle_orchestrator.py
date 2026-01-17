import unittest

from macros.domain.model.macro import Macro, LlmStep, GateStep
from macros.domain.model.cycle import CycleStatus
from macros.domain.services.cycle_orchestrator import CycleOrchestrator
from macros.tests.helpers import FakeAgent, FakeCycleStore, FakeConsole


class TestCycleOrchestrator(unittest.TestCase):
    """Tests for CycleOrchestrator - the core macro execution engine.
    
    Tests cover:
    - Successful execution flow
    - Gate approval/denial
    - Early stopping with --until
    - Agent failure handling
    """

    def _make_orchestrator(
        self,
        agent: FakeAgent,
        store: FakeCycleStore,
        console: FakeConsole,
    ) -> CycleOrchestrator:
        return CycleOrchestrator(
            agent=agent,
            cycle_store=store,
            console=console,
        )

    def test_successful_execution_completes_and_writes_output(self):
        # GIVEN a macro with one LLM step
        macro = Macro(
            macro_id="hello",
            name="Hello",
            steps=[LlmStep(id="greet", prompt="Say: {{INPUT}}")],
        )
        agent = FakeAgent(text="Hello World")
        store = FakeCycleStore()

        # WHEN running the macro
        orchestrator = self._make_orchestrator(agent, store, FakeConsole())
        cycle = orchestrator.run(macro=macro, input_text="World")

        # THEN the cycle completes successfully
        self.assertEqual(cycle.status, CycleStatus.COMPLETED)
        self.assertIsNone(cycle.failure_reason)
        self.assertEqual(len(cycle.results), 1)
        self.assertEqual(cycle.results[0].step_id, "greet")

        # AND output is written to disk
        written_files = [rel for _, rel, _ in store.writes]
        self.assertIn("steps/01-greet.md", written_files)

    def test_gate_denied_cancels_cycle(self):
        # GIVEN a macro with a gate followed by an LLM step
        macro = Macro(
            macro_id="gated",
            name="Gated",
            steps=[
                GateStep(id="confirm", message="Proceed?"),
                LlmStep(id="action", prompt="Do it"),
            ],
        )
        console = FakeConsole(approve=False)  # User denies gate

        # WHEN running the macro
        orchestrator = self._make_orchestrator(FakeAgent(), FakeCycleStore(), console)
        cycle = orchestrator.run(macro=macro, input_text="-")

        # THEN the cycle is cancelled at the gate
        self.assertEqual(cycle.status, CycleStatus.CANCELLED)
        self.assertIn("gate 'confirm'", cycle.failure_reason)
        self.assertEqual(len(cycle.results), 0)  # No LLM steps ran

    def test_stop_after_halts_at_specified_step(self):
        # GIVEN a macro with multiple steps
        macro = Macro(
            macro_id="multi",
            name="Multi",
            steps=[
                LlmStep(id="first", prompt="A"),
                LlmStep(id="second", prompt="B"),
                LlmStep(id="third", prompt="C"),
            ],
        )

        # WHEN running with stop_after="first"
        orchestrator = self._make_orchestrator(FakeAgent(), FakeCycleStore(), FakeConsole())
        cycle = orchestrator.run(macro=macro, input_text="-", stop_after="first")

        # THEN only the first step executes
        self.assertEqual(cycle.status, CycleStatus.COMPLETED)
        self.assertEqual([r.step_id for r in cycle.results], ["first"])

    def test_agent_failure_marks_cycle_failed(self):
        # GIVEN an agent that returns non-zero exit code
        macro = Macro(
            macro_id="fail",
            name="Fail",
            steps=[LlmStep(id="broken", prompt="Fail")],
        )
        agent = FakeAgent(text="Error output", code=1)

        # WHEN running the macro
        orchestrator = self._make_orchestrator(agent, FakeCycleStore(), FakeConsole())
        cycle = orchestrator.run(macro=macro, input_text="-")

        # THEN the cycle is marked as failed with reason
        self.assertEqual(cycle.status, CycleStatus.FAILED)
        self.assertIn("exit code 1", cycle.failure_reason)

    def test_auto_approve_skips_gates(self):
        # GIVEN a macro with a gate
        macro = Macro(
            macro_id="autoapprove",
            name="Auto",
            steps=[
                GateStep(id="confirm", message="Proceed?"),
                LlmStep(id="action", prompt="Do it"),
            ],
        )

        # WHEN running with auto_approve=True
        orchestrator = self._make_orchestrator(FakeAgent(), FakeCycleStore(), FakeConsole(approve=False))
        cycle = orchestrator.run(macro=macro, input_text="-", auto_approve=True)

        # THEN the gate is auto-approved and execution continues
        self.assertEqual(cycle.status, CycleStatus.COMPLETED)
        self.assertEqual(len(cycle.results), 1)

    def test_step_results_preserve_execution_order(self):
        # GIVEN a macro with multiple LLM steps
        macro = Macro(
            macro_id="ordered",
            name="Ordered",
            steps=[
                LlmStep(id="first", prompt="1"),
                LlmStep(id="second", prompt="2"),
                LlmStep(id="third", prompt="3"),
            ],
        )

        # WHEN running the macro
        orchestrator = self._make_orchestrator(FakeAgent(), FakeCycleStore(), FakeConsole())
        cycle = orchestrator.run(macro=macro, input_text="-")

        # THEN results are in execution order
        self.assertEqual(
            [r.step_id for r in cycle.results],
            ["first", "second", "third"]
        )

    def test_cycle_timestamps_are_valid(self):
        # GIVEN a macro
        macro = Macro(
            macro_id="timed",
            name="Timed",
            steps=[LlmStep(id="s1", prompt="X")],
        )

        # WHEN running
        orchestrator = self._make_orchestrator(FakeAgent(), FakeCycleStore(), FakeConsole())
        cycle = orchestrator.run(macro=macro, input_text="-")

        # THEN timestamps are set correctly
        self.assertIsNotNone(cycle.started_at)
        self.assertIsNotNone(cycle.finished_at)
        self.assertLessEqual(cycle.started_at, cycle.finished_at)

    def test_input_text_saved_to_cycle_dir(self):
        # GIVEN a macro and input text
        macro = Macro(
            macro_id="save",
            name="Save",
            steps=[LlmStep(id="s1", prompt="X")],
        )
        store = FakeCycleStore()

        # WHEN running with specific input
        orchestrator = self._make_orchestrator(FakeAgent(), store, FakeConsole())
        orchestrator.run(macro=macro, input_text="My important input")

        # THEN input is saved to input.txt
        input_writes = [(d, r, c) for d, r, c in store.writes if r == "input.txt"]
        self.assertEqual(len(input_writes), 1)
        self.assertEqual(input_writes[0][2], "My important input")
