"""PhaseExecutor -- inner control loop: iterates steps until validation converges."""

from datetime import datetime, timezone
from typing import Callable

from macros.domain.model.agent_config import AgentConfig, resolve_agent_config
from macros.domain.model.context import ExecutionContext
from macros.domain.model.run import PhaseRun, StepRun
from macros.domain.model.step import CommandStep, LlmStep, Step
from macros.domain.model.workflow import Phase
from macros.domain.ports.agent_port import AgentPort
from macros.domain.ports.command_port import CommandPort
from macros.domain.ports.console_port import ConsolePort
from macros.domain.services.prompt_builder import PromptBuilder

AgentFactory = Callable[[AgentConfig], AgentPort]


class PhaseExecutor:
    """Inner control loop: executes a phase's steps and iterates on validation.

    Control theory mapping:
    - Actuator: AgentPort (LlmStep) / CommandPort (CommandStep)
    - Sensor: phase.validation.command
    - Error signal: validation stdout/stderr fed back as {{VALIDATION_OUTPUT}}
    - Gain limit: phase.max_iterations
    - Convergence: validation exit_code == 0
    """

    def __init__(
        self,
        agent_factory: AgentFactory,
        command: CommandPort,
        prompt_builder: PromptBuilder,
        console: ConsolePort,
    ) -> None:
        self._agent_factory = agent_factory
        self._command = command
        self._prompt_builder = prompt_builder
        self._console = console

    def execute(
        self,
        phase: Phase,
        context: ExecutionContext,
        workflow_agent: AgentConfig,
    ) -> PhaseRun:
        started_at = datetime.now(timezone.utc)
        all_step_runs: list[StepRun] = []
        last_output = ""
        last_validation_output: str | None = None

        for iteration in range(1, phase.max_iterations + 1):
            iter_context = ExecutionContext(
                input=context.input,
                phase_outputs=context.phase_outputs,
                iteration=iteration,
                validation_output=context.validation_output if iteration == 1 else last_validation_output,
            )

            self._console.info(
                f"  [{phase.id}] iteration {iteration}/{phase.max_iterations}"
            )

            step_runs = self._execute_steps(
                phase.steps, iter_context, phase, workflow_agent
            )
            all_step_runs.extend(step_runs)

            if step_runs:
                last_output = step_runs[-1].output

            if not phase.validation:
                return PhaseRun(
                    phase_id=phase.id,
                    iteration=iteration,
                    outcome="converged",
                    step_runs=tuple(all_step_runs),
                    output=last_output,
                    validation_output=None,
                    started_at=started_at,
                    finished_at=datetime.now(timezone.utc),
                )

            exit_code, validation_output = self._command.run_command(
                phase.validation.command
            )
            last_validation_output = validation_output

            self._console.info(
                f"  [{phase.id}] validation: exit_code={exit_code}"
            )

            if exit_code == 0:
                return PhaseRun(
                    phase_id=phase.id,
                    iteration=iteration,
                    outcome="converged",
                    step_runs=tuple(all_step_runs),
                    output=last_output,
                    validation_output=validation_output,
                    started_at=started_at,
                    finished_at=datetime.now(timezone.utc),
                )

        return PhaseRun(
            phase_id=phase.id,
            iteration=phase.max_iterations,
            outcome="exhausted",
            step_runs=tuple(all_step_runs),
            output=last_output,
            validation_output=last_validation_output,
            started_at=started_at,
            finished_at=datetime.now(timezone.utc),
        )

    def _execute_steps(
        self,
        steps: tuple[Step, ...],
        context: ExecutionContext,
        phase: Phase,
        workflow_agent: AgentConfig,
    ) -> list[StepRun]:
        results: list[StepRun] = []
        for step in steps:
            started = datetime.now(timezone.utc)

            if isinstance(step, LlmStep):
                agent_config = resolve_agent_config(
                    step.agent, phase.agent, workflow_agent
                )
                agent = self._agent_factory(agent_config)
                prompt = self._prompt_builder.build(
                    template=step.prompt,
                    context=context,
                    step_results=results,
                    max_iterations=phase.max_iterations,
                )
                exit_code, output = agent.run_prompt(prompt)
            elif isinstance(step, CommandStep):
                agent_config = None
                exit_code, output = self._command.run_command(step.command)
            else:
                raise TypeError(f"Unknown step type: {type(step)}")

            finished = datetime.now(timezone.utc)
            results.append(
                StepRun(
                    step_id=step.id,
                    phase_id=phase.id,
                    iteration=context.iteration,
                    started_at=started,
                    finished_at=finished,
                    output=output,
                    exit_code=exit_code,
                    agent_config=agent_config,
                )
            )
        return results
