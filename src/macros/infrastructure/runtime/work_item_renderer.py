"""
Render WorkItemContext to LLM input text.

Templates work with DOMAIN OBJECTS, not dicts.
The domain schema guarantees what fields exist.
"""

from pathlib import Path
from jinja2 import Environment, FileSystemLoader, ChoiceLoader, select_autoescape, TemplateNotFound
from macros.domain.model.work_item import WorkItemContext


class WorkItemRenderer:
    """
    Renders WorkItemContext using Jinja2 templates.
    
    Template lookup order:
    1. User override: .macrocycle/templates/{source_id}.jinja2
    2. Package default: infrastructure/templates/{source_id}.jinja2
    3. Fallback: infrastructure/templates/base.jinja2
    
    Templates receive the DOMAIN OBJECT directly:
    - item: WorkItem
    - description, assignees, labels, priority, project
    - stacktrace: list[StackFrame]
    - comments: list[Comment]
    - linked_items: list[LinkedItem]
    - extras: dict
    """
    
    def __init__(self, workspace: Path, package_templates: Path) -> None:
        user_templates = workspace / ".macrocycle" / "templates"
        
        loaders = []
        if user_templates.exists():
            loaders.append(FileSystemLoader(str(user_templates)))
        loaders.append(FileSystemLoader(str(package_templates)))
        
        self._env = Environment(
            loader=ChoiceLoader(loaders),
            autoescape=select_autoescape(default=False),
            trim_blocks=True,
            lstrip_blocks=True,
        )
        # Register custom filters
        self._env.filters["status_emoji"] = self._status_emoji
        self._env.filters["kind_label"] = self._kind_label
    
    def render(self, context: WorkItemContext) -> str:
        """Render context to text. Falls back to base template if source-specific not found."""
        template_name = f"{context.item.source}.jinja2"
        try:
            template = self._env.get_template(template_name)
        except TemplateNotFound:
            template = self._env.get_template("base.jinja2")
        
        # Pass domain object fields directly — templates use typed access
        return template.render(
            item=context.item,
            description=context.description,
            assignees=context.assignees,
            labels=context.labels,
            priority=context.priority,
            project=context.project,
            stacktrace=context.stacktrace,
            comments=context.comments,
            linked_items=context.linked_items,
            extras=context.extras,
            # Convenience flags
            has_stacktrace=context.has_stacktrace,
            has_comments=context.has_comments,
        )
    
    @staticmethod
    def _status_emoji(status) -> str:
        return {"open": "🔴", "in_progress": "🟡", "closed": "🟢"}.get(status.value, "⚪")
    
    @staticmethod
    def _kind_label(kind) -> str:
        return kind.value.replace("_", " ").title()
