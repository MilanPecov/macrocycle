"""Unit tests for WorkItemRenderer."""

import pytest
from datetime import datetime, timezone
from pathlib import Path
import tempfile

from macros.domain.model.work_item import (
    WorkItem, WorkItemContext, WorkItemKind, WorkItemStatus, StackFrame, Comment
)
from macros.infrastructure.runtime.work_item_renderer import WorkItemRenderer


class TestWorkItemRenderer:
    """WorkItemRenderer tests."""
    
    @pytest.fixture
    def package_templates(self) -> Path:
        """Path to package templates."""
        return Path(__file__).parent.parent.parent / "infrastructure" / "templates"
    
    @pytest.fixture
    def renderer(self, package_templates: Path) -> WorkItemRenderer:
        """Create renderer with package templates only."""
        with tempfile.TemporaryDirectory() as workspace:
            yield WorkItemRenderer(Path(workspace), package_templates)
    
    def _make_item(self, source: str = "sentry") -> WorkItem:
        return WorkItem(
            id="12345",
            source=source,
            kind=WorkItemKind.ERROR,
            title="ValueError in process_request",
            status=WorkItemStatus.OPEN,
            url=f"https://{source}.io/issues/12345",
            created_at=datetime(2024, 1, 15, 10, 30, tzinfo=timezone.utc),
            updated_at=datetime(2024, 1, 16, 14, 0, tzinfo=timezone.utc),
        )
    
    def test_render_minimal_context(self, renderer: WorkItemRenderer) -> None:
        """Render context with minimal data."""
        context = WorkItemContext(item=self._make_item())
        result = renderer.render(context)
        
        assert "ValueError in process_request" in result
        assert "12345" in result
        assert "sentry" in result
        assert "open" in result
    
    def test_render_with_description(self, renderer: WorkItemRenderer) -> None:
        """Render context with description."""
        context = WorkItemContext(
            item=self._make_item(),
            description="Error occurs when user submits empty form",
        )
        result = renderer.render(context)
        
        assert "Description" in result
        assert "empty form" in result
    
    def test_render_with_stacktrace(self, renderer: WorkItemRenderer) -> None:
        """Render context with stacktrace."""
        frame = StackFrame(
            filename="api/handlers.py",
            function="handle_submit",
            lineno=142,
            code="raise ValueError('invalid')",
        )
        context = WorkItemContext(
            item=self._make_item(),
            stacktrace=(frame,),
        )
        result = renderer.render(context)
        
        assert "Stacktrace" in result
        assert "api/handlers.py" in result
        assert "handle_submit" in result
        assert "142" in result
    
    def test_render_with_comments(self, renderer: WorkItemRenderer) -> None:
        """Render context with comments."""
        comment = Comment(
            author="alice",
            body="Looks like a validation issue",
            created_at=datetime(2024, 1, 15, 11, 0, tzinfo=timezone.utc),
        )
        context = WorkItemContext(
            item=self._make_item(),
            comments=(comment,),
        )
        result = renderer.render(context)
        
        assert "Discussion" in result
        assert "alice" in result
        assert "validation issue" in result
    
    def test_render_with_labels_and_assignees(self, renderer: WorkItemRenderer) -> None:
        """Render context with labels and assignees."""
        context = WorkItemContext(
            item=self._make_item(),
            labels=("critical", "backend"),
            assignees=("bob@example.com",),
            priority="high",
            project="api-service",
        )
        result = renderer.render(context)
        
        assert "critical" in result
        assert "backend" in result
        assert "bob@example.com" in result
        assert "high" in result
        assert "api-service" in result
    
    def test_render_github_source(self, renderer: WorkItemRenderer) -> None:
        """Render uses github template for github source."""
        context = WorkItemContext(
            item=self._make_item(source="github"),
            description="Feature request",
        )
        result = renderer.render(context)
        
        # Base template content should be present
        assert "Feature request" in result
        assert "github" in result
    
    def test_render_unknown_source_falls_back_to_base(self, renderer: WorkItemRenderer) -> None:
        """Unknown source falls back to base template."""
        context = WorkItemContext(
            item=self._make_item(source="unknown_source"),
            description="Some issue",
        )
        result = renderer.render(context)
        
        # Should still render without error
        assert "Some issue" in result
        assert "unknown_source" in result
    
    def test_custom_filters_applied(self, renderer: WorkItemRenderer) -> None:
        """Custom filters (status_emoji, kind_label) are available."""
        context = WorkItemContext(item=self._make_item())
        result = renderer.render(context)
        
        # status_emoji filter maps status to emoji
        assert any(emoji in result for emoji in ["🔴", "🟡", "🟢", "⚪"])
    
    def test_user_template_override(self, package_templates: Path) -> None:
        """User templates in workspace override package templates."""
        with tempfile.TemporaryDirectory() as workspace:
            workspace_path = Path(workspace)
            user_templates = workspace_path / ".macrocycle" / "templates"
            user_templates.mkdir(parents=True)
            
            # Create custom template
            custom_template = user_templates / "sentry.jinja2"
            custom_template.write_text("CUSTOM: {{ item.title }}")
            
            renderer = WorkItemRenderer(workspace_path, package_templates)
            context = WorkItemContext(item=self._make_item())
            result = renderer.render(context)
            
            assert result == "CUSTOM: ValueError in process_request"
