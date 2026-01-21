"""Source selection screen."""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, Static, OptionList
from textual.widgets.option_list import Option
from textual.containers import Vertical


# Define source order and display info
SOURCE_INFO = {
    "sentry": {
        "icon": "🔴",
        "description": "Error tracking and performance monitoring",
    },
    "github": {
        "icon": "🐙",
        "description": "Issues and pull requests",
    },
}

SOURCE_ORDER = ["sentry", "github"]


class SourceScreen(Screen):
    """Select a work item source."""
    
    def compose(self) -> ComposeResult:
        yield Header()
        yield Static("🔌 Select a Source", id="title")
        yield Static("Choose a work item source to fetch issues from", id="subtitle")
        yield OptionList(*self._build_options(), id="source-list")
        yield Vertical(
            Static("", id="setup-title"),
            Static("", id="setup-cmd"),
            id="setup-box",
        )
        yield Footer()
    
    def _build_options(self) -> list[Option]:
        registry = self.app.container.source_registry
        config = self.app.container.source_config
        configured = set(config.list_configured_sources())
        available = set(registry.list_sources())
        
        options = []
        # Use defined order, then any remaining sources
        ordered_sources = [s for s in SOURCE_ORDER if s in available]
        ordered_sources.extend(s for s in available if s not in SOURCE_ORDER)
        
        for source_id in ordered_sources:
            is_configured = source_id in configured
            info = SOURCE_INFO.get(source_id, {"icon": "📦", "description": ""})
            
            if is_configured:
                status = "[green]● Ready[/green]"
            else:
                status = "[dim red]○ Setup needed[/dim red]"
            
            label = f"{info['icon']}  {source_id.title():<12} {status}"
            options.append(Option(label, id=source_id, disabled=not is_configured))
        
        return options
    
    def on_mount(self) -> None:
        option_list = self.query_one("#source-list", OptionList)
        if option_list.option_count > 0:
            self._show_hint_for(option_list.get_option_at_index(0).id)
    
    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        source_id = event.option.id
        self.app.state.source_id = source_id
        self.app.state.default_query = self.app.container.source_registry.get_default_query(source_id)
        from macros.tui.screens.issues_screen import IssuesScreen
        self.app.push_screen(IssuesScreen())
    
    def on_option_list_option_highlighted(self, event: OptionList.OptionHighlighted) -> None:
        self._show_hint_for(event.option.id)
    
    def _show_hint_for(self, source_id: str) -> None:
        config = self.app.container.source_config
        setup_box = self.query_one("#setup-box", Vertical)
        setup_title = self.query_one("#setup-title", Static)
        setup_cmd = self.query_one("#setup-cmd", Static)
        
        info = SOURCE_INFO.get(source_id, {"icon": "📦", "description": ""})
        
        if source_id not in config.list_configured_sources():
            missing = config.get_missing_credentials(source_id)
            setup_box.add_class("visible")
            
            # Build the title with description
            title_text = f"[bold yellow]⚠ {source_id.title()} - {info['description']}[/bold yellow]\n"
            title_text += f"[dim]Set these environment variables to connect:[/dim]"
            setup_title.update(title_text)
            
            # Build helpful export commands with actual hints
            env_hints = {
                # Sentry
                "SENTRY_AUTH_TOKEN": ("your-auth-token", "Get from: Settings → API Keys → Auth Tokens"),
                "SENTRY_ORG": ("your-org-slug", "Your organization slug from the URL"),
                "SENTRY_PROJECT": ("your-project", "Project slug from Settings → Projects"),
                # GitHub
                "GITHUB_TOKEN": ("ghp_xxxx", "Get from: Settings → Developer → Personal access tokens"),
                "GITHUB_OWNER": ("owner", "Username or organization name"),
                "GITHUB_REPO": ("repo", "Repository name"),
            }
            
            lines = []
            for var in missing:
                hint, desc = env_hints.get(var, ("your-value", ""))
                lines.append(f"[cyan]export {var}[/cyan]=[green]\"{hint}\"[/green]")
                if desc:
                    lines.append(f"  [dim]# {desc}[/dim]")
            
            setup_cmd.update("\n".join(lines))
        else:
            # Show ready state
            setup_box.add_class("visible")
            setup_title.update(f"[bold green]✓ {source_id.title()} - {info['description']}[/bold green]")
            setup_cmd.update("[dim]Press Enter to select this source[/dim]")
