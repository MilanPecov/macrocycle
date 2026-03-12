"""Formatting functions for CLI presentation."""

from macros.domain.model.run import RunInfo


def format_status(info: RunInfo) -> str:
    return "\n".join([
        f"Last run: {info.workflow_id}",
        f"  Started:   {info.started_at.strftime('%Y-%m-%d %H:%M:%S')}",
        f"  Phases:    {info.phase_count} completed",
        f"  Artifacts: {info.artifacts_dir}",
    ])
