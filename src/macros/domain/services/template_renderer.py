"""Simple template variable substitution."""


class TemplateRenderer:
    """Minimal templating: {{INPUT}}, {{STEP_OUTPUT:<step_id>}}."""

    def render(self, template: str, variables: dict[str, str]) -> str:
        """Replace {{VAR}} placeholders with values from variables dict."""
        out = template
        for k, v in variables.items():
            out = out.replace(f"{{{{{k}}}}}", v)
        return out
