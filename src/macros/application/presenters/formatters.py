"""Formatting functions for CLI presentation."""

from macros.domain.model import CycleInfo, MacroPreview


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
