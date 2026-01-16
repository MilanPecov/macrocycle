from importlib.metadata import version as pkg_version
from pathlib import Path
from typing import Annotated, Optional
import sys

import typer

from macros.application.container import Container
from macros.application.usecases import init_repo, list_macros, run_macro, get_status
from macros.infrastructure.runtime.workspace import get_workspace

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

    for m in macros:
        typer.echo(m)


@app.command()
def status() -> None:
    """Show the most recent cycle status."""
    info = get_status(container)
    if not info:
        container.console.warn("No cycles found. Run: macrocycle run <macro> <input>")
        raise typer.Exit(code=1)

    container.console.info(f"Last cycle: {info.macro_id}")
    container.console.info(f"  Started:   {info.started_at.strftime('%Y-%m-%d %H:%M:%S')}")
    container.console.info(f"  Steps:     {info.step_count} completed")
    container.console.info(f"  Artifacts: {info.cycle_dir}")


@app.command()
def run(
        macro_id: str,
        input_text: Optional[str] = typer.Argument(None),
        input_file: str = typer.Option(None, "--input-file", "-i"),
        yes: bool = typer.Option(False, "--yes", help="Skip gate approvals"),
        until: Optional[str] = typer.Option(None, "--until", help="Stop after this step id"),
        dry_run: bool = typer.Option(False, "--dry-run", help="Preview steps without executing"),
) -> None:
    """Run a macro. Use --dry-run to preview steps first."""
    # Handle dry-run: just show the macro structure
    if dry_run:
        try:
            macro = container.macro_registry.load_macro(macro_id)
        except FileNotFoundError:
            container.console.warn(f"Macro not found: {macro_id}")
            raise typer.Exit(code=1)

        container.console.info(f"Macro: {macro.name} ({len(macro.steps)} steps)")
        for i, step in enumerate(macro.steps, 1):
            container.console.info(f"  {i}. \\[{step.type}] {step.id}")
        raise typer.Exit()

    # Handle stdin via "-" or piped input
    if input_text == "-" or (input_text is None and input_file is None and not sys.stdin.isatty()):
        input_text = sys.stdin.read().strip()

    if input_file:
        input_text = Path(input_file).read_text(encoding="utf-8")

    if not input_text:
        container.console.warn("Provide input_text, --input-file, or pipe via stdin.")
        raise typer.Exit(code=2)

    summary = run_macro(
        container,
        macro_id,
        input_text,
        yes=yes,
        until=until,
    )

    container.console.info("Done.")
    container.console.info(f"Cycle dir: {summary.cycle_dir}")
