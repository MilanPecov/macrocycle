"""CLI entry point - thin orchestration layer."""

from importlib.metadata import version as pkg_version
from pathlib import Path
from typing import Annotated, Optional

import typer

from macros.application.container import Container
from macros.application.presenters import format_status, format_preview
from macros.application.usecases import (
    init_repo,
    list_macros,
    run_macro,
    get_status,
    preview_macro,
)
from macros.domain.exceptions import MacroNotFoundError
from macros.infrastructure.runtime import resolve_input

app = typer.Typer(no_args_is_help=True)


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
    container = Container()
    init_repo(container)
    container.console.info(f"Initialized macros in: {Path.cwd() / '.macrocycle'}")


@app.command(name="list")
def list_cmd() -> None:
    """List available macros in this workspace."""
    container = Container()
    macros = list_macros(container)
    if not macros:
        container.console.warn("No macros found. Run: macrocycle init")
        raise typer.Exit(code=1)
    for macro in macros:
        container.console.echo(macro)


@app.command()
def status() -> None:
    """Show the most recent cycle status."""
    container = Container()
    info = get_status(container)
    if not info:
        container.console.warn("No cycles found. Run: macrocycle run <macro> <input>")
        raise typer.Exit(code=1)
    container.console.echo(format_status(info))


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
    container = Container()
    resolved = resolve_input(input_text, input_file)

    if dry_run:
        try:
            preview = preview_macro(container, macro_id, resolved)
        except MacroNotFoundError:
            container.console.warn(f"Macro not found: {macro_id}")
            raise typer.Exit(code=1)
        container.console.echo(format_preview(preview))
        raise typer.Exit()

    if not resolved:
        container.console.warn("Provide input_text, --input-file, or pipe via stdin.")
        raise typer.Exit(code=2)

    try:
        cycle = run_macro(container, macro_id, resolved, yes=yes, until=until)
    except MacroNotFoundError:
        container.console.warn(f"Macro not found: {macro_id}")
        raise typer.Exit(code=1)

    container.console.info("Done.")
    container.console.info(f"Cycle dir: {cycle.cycle_dir}")
