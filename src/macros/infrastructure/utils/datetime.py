"""Date and time parsing utilities."""

from datetime import datetime


def parse_iso_datetime(s: str) -> datetime:
    """Parse ISO 8601 datetime string, handling 'Z' suffix.
    
    External APIs (Sentry, GitHub) return timestamps with 'Z' suffix
    for UTC. Python's fromisoformat() doesn't handle 'Z' directly,
    so we normalize it to '+00:00'.
    """
    return datetime.fromisoformat(s.replace("Z", "+00:00"))
