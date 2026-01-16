"""CLI entry point - thin orchestration layer."""

from importlib.metadata import version as pkg_version
from typing import Annotated, Optional

import typer

from macros.application.container import Container
from macros.application.usecases import (
    init_repo,
    list_macros,
    run_macro,
    get_status,
    preview_macro,
)
from macros.infrastructure.runtime.utils.input_resolver import resolve_input
from macros.infrastructure.runtime.utils.workspace import get_workspace

app = typer.Typer(no_args_is_help=True)
container = Container()


@app.callback(invoke_without_command=True)
def main(
    version: Annotated[bool, typer.Option("--version", "-V", is_eager=True)] = False,
) -> None:
    """Macrocycle - Ritualized AI agent workflows."""
    if version:
        typer.echo(f"macrocycle {pkg_version('macrocycle')}")
        raise typer.Exit()


@app.command()
def init() -> None:
    """Initialize .macrocycle/ with default macros."""
    init_repo(container)
    container.console.info(f"Initialized macros in: {get_workspace()}/.macrocycle")


@app.command(name="list")
def list_cmd() -> None:
    """List available macros in this workspace."""
    macros = list_macros(container)
    if not macros:
        container.console.warn("No macros found. Run: macrocycle init")
        raise typer.Exit(code=1)
    container.console.print_list(macros)


@app.command()
def status() -> None:
    """Show the most recent cycle status."""
    info = get_status(container)
    if not info:
        container.console.warn("No cycles found. Run: macrocycle run <macro> <input>")
        raise typer.Exit(code=1)
    container.console.print_status(info)


@app.command()
def run(
    macro_id: str,
    input_text: Optional[str] = typer.Argument(None),
    input_file: str = typer.Option(None, "--input-file", "-i"),
    yes: bool = typer.Option(False, "--yes", help="Skip gate approvals"),
    until: Optional[str] = typer.Option(None, "--until", help="Stop after this step id"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview prompts without executing"),
) -> None:
    """Run a macro. Use --dry-run to preview steps first."""
    input_text = resolve_input(input_text, input_file)

    if dry_run:
        try:
            preview = preview_macro(container, macro_id, input_text)
        except FileNotFoundError:
            container.console.warn(f"Macro not found: {macro_id}")
            raise typer.Exit(code=1)
        container.console.print_preview(preview)
        raise typer.Exit()

    if not input_text:
        container.console.warn("Provide input_text, --input-file, or pipe via stdin.")
        raise typer.Exit(code=2)

    cycle = run_macro(container, macro_id, input_text, yes=yes, until=until)
    container.console.info("Done.")
    container.console.info(f"Cycle dir: {cycle.cycle_dir}")
