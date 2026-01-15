from pathlib import Path
from typing import Optional
import typer

from macros.application.container import Container
from macros.application.usecases import init_repo, list_macros, run_macro
from macros.infrastructure.runtime.workspace import get_workspace

app = typer.Typer(no_args_is_help=True)
container = Container()


@app.command()
def init() -> None:
    """Initialize .macrocycle folder and create default fix macro."""
    init_repo(container)
    container.console.info(f"Initialized macros in: {get_workspace()}/.macrocycle")


@app.command(name="list")
def list_cmd() -> None:
    """List available macros."""
    macros = list_macros(container)
    if not macros:
        container.console.warn("No macros found. Run: macrocycle init")
        raise typer.Exit(code=1)

    for m in macros:
        typer.echo(m)


@app.command()
def run(
        macro_id: str,
        input_text: Optional[str] = typer.Argument(None),
        input_file: str = typer.Option(None, "--input-file", "-i"),
        yes: bool = typer.Option(False, "--yes", help="Skip gate approvals"),
        until: Optional[str] = typer.Option(None, "--until", help="Stop after this step id"),
) -> None:
    """Run a macro with optional gate approval."""
    if input_text is None and input_file is None:
        container.console.warn("Provide input_text or --input-file.")
        raise typer.Exit(code=2)

    if input_file:
        input_text = Path(input_file).read_text(encoding="utf-8")

    summary = run_macro(
        container,
        macro_id,
        input_text,
        yes=yes,
        until=until,
    )

    container.console.info("Done.")
    container.console.info(f"Cycle dir: {summary.cycle_dir}")
