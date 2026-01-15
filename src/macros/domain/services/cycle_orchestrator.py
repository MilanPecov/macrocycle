from datetime import datetime, UTC

from macros.domain.model.macro import Macro, LlmStep, GateStep
from macros.domain.model.cycle import Cycle, CycleStatus, StepRun
from macros.domain.ports.agent_port import AgentPort
from macros.domain.ports.cycle_store_port import CycleStorePort
from macros.domain.ports.console_port import ConsolePort
from macros.domain.services.prompt_builder import PromptBuilder


class CycleOrchestrator:
    """Orchestrates the execution of a macro cycle.

    The run() method implements the core algorithm:
    1. Create cycle directory and save input
    2. For each step in the macro:
       - If gate: handle approval
       - If llm: execute prompt and save output
    3. Return cycle with final status
    """

    def __init__(
        self,
        agent: AgentPort,
        cycle_store: CycleStorePort,
        console: ConsolePort,
        prompt_builder: PromptBuilder,
    ):
        self._agent = agent
        self._store = cycle_store
        self._console = console
        self._prompt_builder = prompt_builder

    # -------------------------------------------------------------------------
    # Main entry point
    # -------------------------------------------------------------------------

    def run(
        self,
        macro: Macro,
        input_text: str,
        *,
        auto_approve: bool = False,
        stop_after: str | None = None,
    ) -> Cycle:
        """Execute a macro and return the cycle.

        Args:
            macro: The macro definition to execute
            input_text: User-provided input for the cycle
            auto_approve: If True, automatically approve all gates
            stop_after: If set, stop after completing this step ID
        """
        # Initialize cycle
        started_at = datetime.now(UTC)
        cycle_dir = self._store.create_cycle_dir(macro.macro_id)
        self._store.write_text(cycle_dir, "input.txt", input_text)
        results: list[StepRun] = []
        failure_reason: str | None = None
        status = CycleStatus.RUNNING

        self._console.info(f"Cycle: {macro.name} ({macro.engine})")
        self._console.info(f"Artifacts: {cycle_dir}")

        # Execute steps
        for idx, step in enumerate(macro.steps, start=1):
            self._log_step_start(idx, len(macro.steps), step.id, step.type)

            if isinstance(step, GateStep):
                should_continue = self._handle_gate(step, auto_approve)
                if not should_continue:
                    status = CycleStatus.CANCELLED
                    failure_reason = f"Cancelled by user at gate '{step.id}'"
                    break
                if self._should_stop(step.id, stop_after):
                    status = CycleStatus.COMPLETED
                    break
                continue

            if isinstance(step, LlmStep):
                step_run = self._execute_llm_step(step, macro, input_text, results)
                results.append(step_run)
                self._save_step_output(cycle_dir, idx, step.id, step_run.output_text)

                if step_run.exit_code != 0:
                    self._console.warn(f"Agent returned non-zero exit code: {step_run.exit_code}. Stopping.")
                    status = CycleStatus.FAILED
                    failure_reason = f"Agent failed at step '{step.id}' with exit code {step_run.exit_code}"
                    break

                if self._should_stop(step.id, stop_after):
                    status = CycleStatus.COMPLETED
                    break
        else:
            # Loop completed without break - all steps succeeded
            status = CycleStatus.COMPLETED

        return self._build_cycle(
            cycle_dir=cycle_dir,
            macro=macro,
            results=results,
            status=status,
            failure_reason=failure_reason,
            started_at=started_at,
        )

    # -------------------------------------------------------------------------
    # Step handlers
    # -------------------------------------------------------------------------

    def _handle_gate(self, step: GateStep, auto_approve: bool) -> bool:
        """Handle a gate step. Returns True if approved, False to stop."""
        if auto_approve:
            self._console.info("Gate auto-approved (--yes).")
            return True

        message = step.message
        approved = self._console.confirm(message, default=True)

        if not approved:
            self._console.warn("Stopped by user at gate.")
        return approved

    def _execute_llm_step(
        self,
        step: LlmStep,
        macro: Macro,
        input_text: str,
        previous_results: list[StepRun],
    ) -> StepRun:
        """Execute an LLM step and return the result."""
        prompt = self._prompt_builder.build(
            step=step,
            input_text=input_text,
            previous_results=previous_results,
            include_previous_context=macro.include_previous_outputs,
        )

        started = datetime.now(UTC)
        exit_code, output = self._agent.run_prompt(prompt)
        finished = datetime.now(UTC)

        return StepRun(
            step_id=step.id,
            started_at=started,
            finished_at=finished,
            output_text=output,
            engine=macro.engine,
            exit_code=exit_code,
        )

    # -------------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------------

    def _log_step_start(self, idx: int, total: int, step_id: str, step_type: str) -> None:
        self._console.info(f"[{idx}/{total}] Step: {step_id} ({step_type})")

    def _should_stop(self, step_id: str, stop_after: str | None) -> bool:
        if stop_after == step_id:
            self._console.warn(f"Stopping after --until {stop_after}")
            return True
        return False

    def _save_step_output(self, cycle_dir: str, idx: int, step_id: str, output: str) -> None:
        filename = f"steps/{idx:02d}-{step_id}.md"
        self._store.write_text(cycle_dir, filename, output)

    def _build_cycle(
        self,
        cycle_dir: str,
        macro: Macro,
        results: list[StepRun],
        status: CycleStatus,
        failure_reason: str | None,
        started_at: datetime,
    ) -> Cycle:
        finished_at = datetime.now(UTC) if status != CycleStatus.RUNNING else None
        return Cycle(
            cycle_id=cycle_dir.split("/")[-1],
            macro_id=macro.macro_id,
            engine=macro.engine,
            cycle_dir=cycle_dir,
            status=status,
            failure_reason=failure_reason,
            started_at=started_at,
            finished_at=finished_at,
            results=results,
        )
