"""Sentry source adapter."""

import urllib.parse
import urllib.error
from macros.domain.model.work_item import (
    WorkItem, WorkItemContext, WorkItemKind, WorkItemStatus,
    StackFrame,
)
from macros.domain.ports.source_config_port import SourceConfig
from macros.domain.exceptions import WorkItemNotFoundError
from macros.infrastructure.sources.http_client import HttpClient
from macros.infrastructure.utils import parse_iso_datetime


class SentrySourceAdapter:
    """Implements WorkItemSourcePort for Sentry.
    
    Handles HTTP communication with Sentry API and maps Sentry JSON to domain objects.
    """
    
    def __init__(self, config: SourceConfig) -> None:
        self._org = config.require("org")
        self._project = config.get("project")
        self._base_url = config.get("base_url") or "https://sentry.io"
        self._http = HttpClient({"Authorization": f"Bearer {config.require('token')}"})
    
    @property
    def source_id(self) -> str:
        return "sentry"
    
    @property
    def supported_kinds(self) -> frozenset[WorkItemKind]:
        return frozenset({WorkItemKind.ERROR})
    
    def discover(self, query: str, limit: int) -> list[WorkItem]:
        params = {"query": query, "limit": str(limit), "project": self._project} if self._project else {"query": query, "limit": str(limit)}
        url = f"{self._base_url}/api/0/organizations/{self._org}/issues/?{urllib.parse.urlencode(params)}"
        data = self._http.get_json(url)
        return [self._map_to_work_item(issue) for issue in data]
    
    def resolve(self, item_id: str) -> WorkItemContext:
        try:
            issue = self._http.get_json(f"{self._base_url}/api/0/issues/{item_id}/")
            event = self._http.get_json(f"{self._base_url}/api/0/issues/{item_id}/events/latest/")
        except urllib.error.HTTPError as e:
            if e.code == 404:
                raise WorkItemNotFoundError(item_id, "sentry")
            raise
        
        return WorkItemContext(
            item=self._map_to_work_item(issue),
            description=issue.get("metadata", {}).get("value"),
            assignees=tuple(
                a["email"] for a in (issue.get("assignedTo") or [])
                if isinstance(a, dict) and a.get("email")
            ),
            labels=tuple(t["value"] for t in event.get("tags", []) if t.get("key") == "level"),
            priority=self._map_level_to_priority(issue.get("level", "error")),
            project=issue["project"]["slug"],
            stacktrace=self._extract_stacktrace(event),
            comments=(),
            linked_items=(),
            extras={
                "culprit": issue.get("culprit"),
                "event_count": int(issue.get("count", 0)),
                "user_count": issue.get("userCount", 0),
                "tags": {t["key"]: t["value"] for t in event.get("tags", [])},
                "browser": self._get_tag(event, "browser"),
                "os": self._get_tag(event, "os"),
                "request": self._extract_request(event),
            },
            suggested_macro="fix",
        )
    
    def _map_to_work_item(self, issue: dict) -> WorkItem:
        return WorkItem(
            id=issue["id"],
            source="sentry",
            kind=WorkItemKind.ERROR,
            title=issue["title"],
            status=self._map_status(issue.get("status", "unresolved")),
            url=issue.get("permalink") or f"https://sentry.io/issues/{issue['id']}/",
            created_at=parse_iso_datetime(issue["firstSeen"]),
            updated_at=parse_iso_datetime(issue["lastSeen"]),
        )
    
    def _map_status(self, sentry_status: str) -> WorkItemStatus:
        return {
            "unresolved": WorkItemStatus.OPEN,
            "resolved": WorkItemStatus.CLOSED,
            "ignored": WorkItemStatus.CLOSED,
        }.get(sentry_status, WorkItemStatus.OPEN)
    
    def _map_level_to_priority(self, level: str) -> str:
        return {"fatal": "critical", "error": "high", "warning": "medium", "info": "low"}.get(level, "medium")
    
    def _extract_stacktrace(self, event: dict) -> tuple[StackFrame, ...]:
        frames = []
        for entry in event.get("entries", []):
            if entry.get("type") != "exception":
                continue
            for exc in entry.get("data", {}).get("values", []):
                for f in exc.get("stacktrace", {}).get("frames", []):
                    frames.append(StackFrame(
                        filename=f.get("filename", "<unknown>"),
                        function=f.get("function", "<unknown>"),
                        lineno=f.get("lineNo", 0),
                        code=self._find_context_line(f),
                        context_before=tuple(f.get("preContext", []) or []),
                        context_after=tuple(f.get("postContext", []) or []),
                    ))
        return tuple(frames)
    
    def _find_context_line(self, frame: dict) -> str | None:
        for ctx in frame.get("context", []):
            if ctx[0] == frame.get("lineNo"):
                return ctx[1]
        return None
    
    def _extract_request(self, event: dict) -> dict | None:
        for entry in event.get("entries", []):
            if entry.get("type") == "request":
                return entry.get("data")
        return None
    
    def _get_tag(self, event: dict, key: str) -> str | None:
        for tag in event.get("tags", []):
            if tag.get("key") == key:
                return tag.get("value")
        return None
