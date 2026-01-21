"""CLI entry point - thin orchestration layer."""

from importlib.metadata import version as pkg_version
from pathlib import Path
from typing import Annotated, Optional

import typer

from macros.application.container import Container
from macros.application.presenters import (
    format_status,
    format_preview,
    format_work_items_table,
    format_sources_status,
)
from macros.application.usecases import (
    init_repo,
    list_macros,
    run_macro,
    get_status,
    preview_macro,
    discover_work_items,
    fix_work_item,
)
from macros.domain.exceptions import (
    MacroNotFoundError,
    SourceNotFoundError,
    SourceNotConfiguredError,
    WorkItemNotFoundError,
)
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


@app.command()
def tui() -> None:
    """Launch interactive TUI for batch processing."""
    from macros.tui import run_tui
    run_tui()


# Work item subcommands

work_app = typer.Typer(no_args_is_help=True)
app.add_typer(work_app, name="work", help="Work with external issue sources.")


@work_app.command(name="list")
def work_list_cmd(
    query: Annotated[str, typer.Option("--query", "-q", help="Source-specific query")] = "",
    limit: Annotated[int, typer.Option("--limit", "-n", help="Max results")] = 10,
    source: Annotated[str, typer.Option("--source", "-s", help="Source: sentry, github")] = "sentry",
) -> None:
    """List work items from an external source."""
    container = Container()
    actual_query = query or container.source_registry.get_default_query(source)

    try:
        items = discover_work_items(container, source, actual_query, limit)
    except (SourceNotFoundError, SourceNotConfiguredError) as e:
        container.console.warn(str(e))
        raise typer.Exit(code=1)

    container.console.echo(format_work_items_table(items))


@work_app.command(name="fix")
def work_fix_cmd(
    item_id: Annotated[str, typer.Argument(help="Work item ID from the source")],
    source: Annotated[str, typer.Option("--source", "-s", help="Source: sentry, github")] = "sentry",
    macro: Annotated[Optional[str], typer.Option("--macro", "-m", help="Override suggested macro")] = None,
    yes: Annotated[bool, typer.Option("--yes", help="Skip gate approvals")] = False,
    until: Annotated[Optional[str], typer.Option("--until", help="Stop after step")] = None,
) -> None:
    """Fetch work item context and run fix macro."""
    container = Container()

    try:
        cycle = fix_work_item(container, source, item_id, macro_id=macro, yes=yes, until=until)
    except (SourceNotFoundError, SourceNotConfiguredError, WorkItemNotFoundError) as e:
        container.console.warn(str(e))
        raise typer.Exit(code=1)
    except MacroNotFoundError as e:
        container.console.warn(f"Macro not found: {e}")
        raise typer.Exit(code=1)

    container.console.info("Done.")
    container.console.info(f"Cycle dir: {cycle.cycle_dir}")


@work_app.command(name="sources")
def work_sources_cmd() -> None:
    """List available and configured work item sources."""
    container = Container()
    output = format_sources_status(
        available=container.source_registry.list_sources(),
        configured=container.source_config.list_configured_sources(),
        get_missing=container.source_config.get_missing_credentials,
    )
    container.console.echo(output)
