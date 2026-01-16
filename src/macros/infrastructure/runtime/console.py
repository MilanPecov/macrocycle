from __future__ import annotations

from typing import TYPE_CHECKING

import typer
from rich.console import Console

from macros.domain.ports.console_port import ConsolePort

if TYPE_CHECKING:
    from macros.domain.model import CycleInfo, MacroPreview


class StdConsoleAdapter(ConsolePort):
    """Standard console adapter using Rich for formatting and Typer for prompts."""

    def __init__(self):
        self._c = Console()

    def info(self, msg: str) -> None:
        self._c.print(f"[bold cyan]INFO[/] {msg}")

    def warn(self, msg: str) -> None:
        self._c.print(f"[bold yellow]WARN[/] {msg}")

    def echo(self, msg: str) -> None:
        self._c.print(msg)

    def confirm(self, msg: str, default: bool = True) -> bool:
        return typer.confirm(msg, default=default)

    def print_list(self, items: list[str]) -> None:
        for item in items:
            self._c.print(item)

    def print_status(self, info: "CycleInfo") -> None:
        self.info(f"Last cycle: {info.macro_id}")
        self.info(f"  Started:   {info.started_at.strftime('%Y-%m-%d %H:%M:%S')}")
        self.info(f"  Steps:     {info.step_count} completed")
        self.info(f"  Artifacts: {info.cycle_dir}")

    def print_preview(self, preview: "MacroPreview") -> None:
        sep = "=" * 60
        self.echo(f"\n{sep}")
        self.echo(f"MACRO: {preview.name} ({preview.engine})")
        self.echo(sep)
        if preview.include_previous_context:
            self.echo("(previous step outputs will be appended as context)\n")

        for step in preview.steps:
            self.echo(f"\n--- Step {step.index}: {step.step_id} \\[{step.step_type}] ---\n")
            self.echo(step.content)

        self.echo(f"\n{sep}\n")
