"""GitHub Issues/PRs source adapter."""

import urllib.parse
import urllib.error
from macros.domain.model.work_item import (
    WorkItem, WorkItemContext, WorkItemKind, WorkItemStatus,
    Comment, LinkedItem,
)
from macros.domain.ports.source_config_port import SourceConfig
from macros.domain.exceptions import WorkItemNotFoundError
from macros.infrastructure.sources.http_client import HttpClient
from macros.infrastructure.utils import parse_iso_datetime


class GitHubSourceAdapter:
    """Implements WorkItemSourcePort for GitHub Issues and PRs."""
    
    def __init__(self, config: SourceConfig) -> None:
        self._owner = config.require("owner")
        self._repo = config.require("repo")
        self._http = HttpClient({
            "Authorization": f"Bearer {config.require('token')}",
            "Accept": "application/vnd.github+json",
        })
    
    @property
    def source_id(self) -> str:
        return "github"
    
    @property
    def supported_kinds(self) -> frozenset[WorkItemKind]:
        return frozenset({WorkItemKind.BUG, WorkItemKind.FEATURE, WorkItemKind.REVIEW})
    
    def discover(self, query: str, limit: int) -> list[WorkItem]:
        full_query = f"{query} repo:{self._owner}/{self._repo}"
        url = f"https://api.github.com/search/issues?q={urllib.parse.quote(full_query)}&per_page={limit}"
        data = self._http.get_json(url)
        return [self._map_to_work_item(item) for item in data.get("items", [])]
    
    def resolve(self, item_id: str) -> WorkItemContext:
        try:
            issue = self._http.get_json(
                f"https://api.github.com/repos/{self._owner}/{self._repo}/issues/{item_id}"
            )
            comments_data = self._http.get_json(
                f"https://api.github.com/repos/{self._owner}/{self._repo}/issues/{item_id}/comments"
            )
        except urllib.error.HTTPError as e:
            if e.code == 404:
                raise WorkItemNotFoundError(item_id, "github")
            raise
        
        return WorkItemContext(
            item=self._map_to_work_item(issue),
            description=issue.get("body", ""),
            assignees=tuple(a["login"] for a in issue.get("assignees", [])),
            labels=tuple(l["name"] for l in issue.get("labels", [])),
            priority=self._infer_priority(issue),
            project=self._repo,
            stacktrace=(),
            comments=tuple(
                Comment(
                    author=c["user"]["login"],
                    body=c["body"],
                    created_at=parse_iso_datetime(c["created_at"]),
                )
                for c in comments_data
            ),
            linked_items=self._extract_linked_prs(issue),
            extras={
                "reactions": issue.get("reactions", {}),
                "milestone": issue.get("milestone", {}).get("title") if issue.get("milestone") else None,
            },
            suggested_macro=self._suggest_macro(issue),
        )
    
    def _map_to_work_item(self, issue: dict) -> WorkItem:
        return WorkItem(
            id=str(issue["number"]),
            source="github",
            kind=self._infer_kind(issue),
            title=issue["title"],
            status=WorkItemStatus.OPEN if issue["state"] == "open" else WorkItemStatus.CLOSED,
            url=issue["html_url"],
            created_at=parse_iso_datetime(issue["created_at"]),
            updated_at=parse_iso_datetime(issue["updated_at"]),
        )
    
    def _infer_kind(self, issue: dict) -> WorkItemKind:
        if "pull_request" in issue:
            return WorkItemKind.REVIEW
        labels = [l["name"].lower() for l in issue.get("labels", [])]
        if "bug" in labels:
            return WorkItemKind.BUG
        return WorkItemKind.FEATURE
    
    def _infer_priority(self, issue: dict) -> str | None:
        labels = [l["name"].lower() for l in issue.get("labels", [])]
        if "critical" in labels or "p0" in labels:
            return "critical"
        if "high" in labels or "p1" in labels:
            return "high"
        if "low" in labels or "p3" in labels:
            return "low"
        return "medium"
    
    def _suggest_macro(self, issue: dict) -> str:
        if "pull_request" in issue:
            return "review"
        kind = self._infer_kind(issue)
        return "fix" if kind == WorkItemKind.BUG else "implement"
    
    def _extract_linked_prs(self, issue: dict) -> tuple[LinkedItem, ...]:
        return ()
