"""File-based macro storage."""

from pathlib import Path
from importlib import resources

from macros.domain.model.macro import Macro
from macros.domain.ports.macro_registry_port import MacroRegistryPort
from macros.domain.exceptions import MacroNotFoundError
from macros.infrastructure.persistence.mappers import MacroJsonMapper
from macros.infrastructure.runtime.utils.workspace import get_workspace


_DEFAULTS_PACKAGE = "macros.infrastructure.persistence.defaults"


class FileMacroStore(MacroRegistryPort):
    """Loads macros from repo-local files or packaged defaults.

    This adapter handles IO only - validation is a domain concern
    handled by use cases via MacroValidator.
    """

    @property
    def _macro_dir(self) -> Path:
        return get_workspace() / ".macrocycle" / "macros"

    def list_macros(self) -> list[str]:
        """List all available macro IDs (repo-local only)."""
        if not self._macro_dir.exists():
            return []
        return sorted([p.stem for p in self._macro_dir.glob("*.json")])

    def load_macro(self, macro_id: str) -> Macro:
        """Load a macro by ID.

        Preference order:
        1) Repo-local definition under `.macrocycle/macros/<id>.json`
        2) Packaged default (if available)
        
        Raises:
            MacroNotFoundError: If macro not found
        """
        # Try repo-local first
        path = self._macro_dir / f"{macro_id}.json"
        if path.exists():
            text = path.read_text(encoding="utf-8")
            return MacroJsonMapper.from_json(text)

        # Fallback to packaged defaults
        macro = self._load_packaged_default(macro_id)
        if macro is not None:
            return macro

        raise MacroNotFoundError(f"Macro not found: {macro_id}")

    def init_default_macros(self) -> None:
        """Seed repo with any packaged default macros that are missing."""
        self._macro_dir.mkdir(parents=True, exist_ok=True)

        for name in self._list_packaged_defaults():
            target = self._macro_dir / f"{name}.json"
            if not target.exists():
                text = self._load_packaged_default_text(name)
                if text:
                    target.write_text(text, encoding="utf-8")

    def _list_packaged_defaults(self) -> list[str]:
        """List all packaged default macro names."""
        base = resources.files(_DEFAULTS_PACKAGE)
        return sorted([
            p.stem for p in base.iterdir()  # type: ignore[attr-defined]
            if p.is_file() and p.suffix == ".json"
        ])

    def _load_packaged_default(self, macro_id: str) -> Macro | None:
        """Load a packaged default macro by ID, or None if not found."""
        text = self._load_packaged_default_text(macro_id)
        if text is None:
            return None
        return MacroJsonMapper.from_json(text)

    def _load_packaged_default_text(self, macro_id: str) -> str | None:
        """Load raw JSON text for a packaged default macro."""
        filename = f"{macro_id}.json"
        try:
            with resources.as_file(resources.files(_DEFAULTS_PACKAGE) / filename) as p:  # type: ignore[attr-defined]
                return p.read_text(encoding="utf-8")
        except (FileNotFoundError, TypeError):
            return None
