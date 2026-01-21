"""Formatting functions for CLI presentation."""

from typing import Callable
from macros.domain.model import CycleInfo, MacroPreview, WorkItem


def format_status(info: CycleInfo) -> str:
    """Format cycle status for display."""
    return "\n".join([
        f"Last cycle: {info.macro_id}",
        f"  Started:   {info.started_at.strftime('%Y-%m-%d %H:%M:%S')}",
        f"  Steps:     {info.step_count} completed",
        f"  Artifacts: {info.cycle_dir}",
    ])


def format_preview(preview: MacroPreview) -> str:
    """Format macro preview for display."""
    sep = "=" * 60
    lines = [f"\n{sep}", f"MACRO: {preview.name} ({preview.engine})", sep]

    if preview.include_previous_context:
        lines.append("(previous step outputs will be appended as context)\n")

    for step in preview.steps:
        lines.append(f"\n--- Step {step.index}: {step.step_id} \\[{step.step_type}] ---\n")
        lines.append(step.content)

    lines.append(f"\n{sep}\n")
    return "\n".join(lines)


def format_work_items_table(items: list[WorkItem]) -> str:
    """Format work items as table. Works for any source."""
    if not items:
        return "No work items found."

    id_w = max(len(i.id) for i in items)
    src_w = max(len(i.source) for i in items)
    kind_w = max(len(i.kind.value) for i in items)

    lines = [
        f"{'ID':<{id_w}}  {'SOURCE':<{src_w}}  {'KIND':<{kind_w}}  {'STATUS':<12}  TITLE",
        "-" * (id_w + src_w + kind_w + 60),
    ]

    for i in items:
        title = i.title[:45] + "..." if len(i.title) > 45 else i.title
        lines.append(
            f"{i.id:<{id_w}}  {i.source:<{src_w}}  {i.kind.value:<{kind_w}}  {i.status.value:<12}  {title}"
        )

    return "\n".join(lines)


def format_sources_status(
    available: list[str],
    configured: list[str],
    get_missing: Callable[[str], list[str]],
) -> str:
    """Format source availability status for display."""
    if not available:
        return "No sources available."

    lines = ["Available sources:"]
    for source in available:
        if source in configured:
            status = "✓ configured"
        else:
            missing = get_missing(source)
            hint = f" (set: {', '.join(missing)})" if missing else ""
            status = f"✗ not configured{hint}"
        lines.append(f"  {source}: {status}")

    return "\n".join(lines)
