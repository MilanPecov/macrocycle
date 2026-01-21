"""Unit tests for WorkItem domain model."""

import pytest
from datetime import datetime, timezone
from macros.domain.model.work_item import (
    WorkItem, WorkItemKind, WorkItemStatus, WorkItemContext, StackFrame, Comment, LinkedItem
)


class TestWorkItem:
    """WorkItem value object tests."""
    
    def test_valid_work_item_creation(self) -> None:
        """WorkItem with valid data creates successfully."""
        item = WorkItem(
            id="123",
            source="sentry",
            kind=WorkItemKind.ERROR,
            title="NullPointerException",
            status=WorkItemStatus.OPEN,
            url="https://sentry.io/issues/123",
            created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
            updated_at=datetime(2024, 1, 2, tzinfo=timezone.utc),
        )
        assert item.id == "123"
        assert item.source == "sentry"
        assert item.kind == WorkItemKind.ERROR
    
    def test_empty_id_raises_error(self) -> None:
        """WorkItem with empty id raises ValueError."""
        with pytest.raises(ValueError, match="id cannot be empty"):
            WorkItem(
                id="",
                source="sentry",
                kind=WorkItemKind.ERROR,
                title="Test",
                status=WorkItemStatus.OPEN,
                url="https://test.com",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
    
    def test_empty_source_raises_error(self) -> None:
        """WorkItem with empty source raises ValueError."""
        with pytest.raises(ValueError, match="source cannot be empty"):
            WorkItem(
                id="123",
                source="",
                kind=WorkItemKind.ERROR,
                title="Test",
                status=WorkItemStatus.OPEN,
                url="https://test.com",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
    
    def test_work_item_is_immutable(self) -> None:
        """WorkItem is frozen dataclass."""
        item = WorkItem(
            id="123",
            source="sentry",
            kind=WorkItemKind.ERROR,
            title="Test",
            status=WorkItemStatus.OPEN,
            url="https://test.com",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        with pytest.raises(Exception):  # FrozenInstanceError
            item.title = "Changed"  # type: ignore


class TestWorkItemContext:
    """WorkItemContext tests."""
    
    def _make_item(self) -> WorkItem:
        return WorkItem(
            id="123",
            source="test",
            kind=WorkItemKind.ERROR,
            title="Test Error",
            status=WorkItemStatus.OPEN,
            url="https://test.com/123",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
    
    def test_minimal_context(self) -> None:
        """Context with just item is valid."""
        context = WorkItemContext(item=self._make_item())
        assert context.item.id == "123"
        assert context.description is None
        assert context.stacktrace == ()
        assert context.comments == ()
    
    def test_has_stacktrace_property(self) -> None:
        """has_stacktrace returns True when stacktrace present."""
        frame = StackFrame(filename="app.py", function="main", lineno=42)
        context = WorkItemContext(item=self._make_item(), stacktrace=(frame,))
        assert context.has_stacktrace is True
        
        empty_context = WorkItemContext(item=self._make_item())
        assert empty_context.has_stacktrace is False
    
    def test_has_comments_property(self) -> None:
        """has_comments returns True when comments present."""
        comment = Comment(
            author="user",
            body="Fixed in v2",
            created_at=datetime.now(timezone.utc),
        )
        context = WorkItemContext(item=self._make_item(), comments=(comment,))
        assert context.has_comments is True
        
        empty_context = WorkItemContext(item=self._make_item())
        assert empty_context.has_comments is False
    
    def test_context_with_full_data(self) -> None:
        """Context with all fields populated."""
        frame = StackFrame(
            filename="app.py",
            function="handle_request",
            lineno=42,
            code="raise ValueError('test')",
            context_before=("def handle_request():",),
            context_after=("except:",),
        )
        comment = Comment(
            author="dev",
            body="Looking into this",
            created_at=datetime.now(timezone.utc),
        )
        linked = LinkedItem(
            kind="pr",
            id="456",
            title="Fix the bug",
            url="https://github.com/org/repo/pull/456",
            status="merged",
        )
        
        context = WorkItemContext(
            item=self._make_item(),
            description="Error when processing request",
            assignees=("dev@example.com",),
            labels=("error", "high"),
            priority="high",
            project="backend",
            stacktrace=(frame,),
            comments=(comment,),
            linked_items=(linked,),
            extras={"browser": "Chrome 120"},
            suggested_macro="fix",
        )
        
        assert context.description == "Error when processing request"
        assert "dev@example.com" in context.assignees
        assert context.priority == "high"
        assert len(context.stacktrace) == 1
        assert context.stacktrace[0].filename == "app.py"
        assert context.extras["browser"] == "Chrome 120"


class TestStackFrame:
    """StackFrame value object tests."""
    
    def test_minimal_frame(self) -> None:
        """Frame with required fields only."""
        frame = StackFrame(filename="test.py", function="test", lineno=1)
        assert frame.filename == "test.py"
        assert frame.code is None
        assert frame.context_before == ()
    
    def test_frame_with_context(self) -> None:
        """Frame with code context."""
        frame = StackFrame(
            filename="app.py",
            function="main",
            lineno=10,
            code="x = y + 1",
            context_before=("# add values", "y = 5"),
            context_after=("return x",),
        )
        assert frame.code == "x = y + 1"
        assert len(frame.context_before) == 2
        assert len(frame.context_after) == 1


class TestWorkItemKind:
    """WorkItemKind enum tests."""
    
    def test_all_kinds_have_values(self) -> None:
        """Each kind has a string value."""
        for kind in WorkItemKind:
            assert isinstance(kind.value, str)
            assert len(kind.value) > 0
    
    def test_expected_kinds_exist(self) -> None:
        """Expected kinds are available."""
        kinds = {k.value for k in WorkItemKind}
        assert "error" in kinds
        assert "bug" in kinds
        assert "feature" in kinds
        assert "task" in kinds


class TestWorkItemStatus:
    """WorkItemStatus enum tests."""
    
    def test_all_statuses_have_values(self) -> None:
        """Each status has a string value."""
        for status in WorkItemStatus:
            assert isinstance(status.value, str)
    
    def test_expected_statuses_exist(self) -> None:
        """Expected statuses are available."""
        statuses = {s.value for s in WorkItemStatus}
        assert "open" in statuses
        assert "closed" in statuses
