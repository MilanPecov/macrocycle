"""CLI entry point - thin orchestration layer."""

from importlib.metadata import version as pkg_version
from pathlib import Path
from typing import Annotated, Optional

import typer

from macros.application.container import Container
from macros.application.presenters import format_status
from macros.application.usecases import (
    init_workspace,
    list_workflows,
    run_workflow,
    get_status,
)
from macros.domain.exceptions import WorkflowNotFoundError
from macros.infrastructure.runtime import resolve_input

app = typer.Typer(no_args_is_help=True)


@app.callback(invoke_without_command=True)
def main(
    version: Annotated[bool, typer.Option("--version", "-V", is_eager=True)] = False,
) -> None:
    """Macrocycle - closed-loop AI agent workflows."""
    if version:
        typer.echo(f"macrocycle {pkg_version('macrocycle')}")
        raise typer.Exit()


@app.command()
def init() -> None:
    """Initialize .macrocycle/ with default workflows."""
    container = Container()
    init_workspace(container)
    container.console.info(f"Initialized workflows in: {Path.cwd() / '.macrocycle'}")


@app.command(name="list")
def list_cmd() -> None:
    """List available workflows in this workspace."""
    container = Container()
    workflows = list_workflows(container)
    if not workflows:
        container.console.warn("No workflows found. Run: macrocycle init")
        raise typer.Exit(code=1)
    for w in workflows:
        container.console.echo(w)


@app.command()
def status() -> None:
    """Show the most recent run status."""
    container = Container()
    info = get_status(container)
    if not info:
        container.console.warn("No runs found. Run: macrocycle run <workflow> <input>")
        raise typer.Exit(code=1)
    container.console.echo(format_status(info))


@app.command()
def run(
    workflow_id: str,
    input_text: Optional[str] = typer.Argument(None),
    input_file: str = typer.Option(None, "--input-file", "-i"),
    until: Optional[str] = typer.Option(None, "--until", help="Stop after this phase id"),
) -> None:
    """Run a workflow with the given input."""
    container = Container()
    resolved = resolve_input(input_text, input_file)

    if not resolved:
        container.console.warn("Provide input_text, --input-file, or pipe via stdin.")
        raise typer.Exit(code=2)

    try:
        result = run_workflow(container, workflow_id, resolved, stop_after=until)
    except WorkflowNotFoundError:
        container.console.warn(f"Workflow not found: {workflow_id}")
        raise typer.Exit(code=1)

    container.console.info(f"Done. Status: {result.status.value}")
    container.console.info(f"Run dir: {result.artifacts_dir}")
