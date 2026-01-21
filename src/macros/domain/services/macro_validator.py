"""Macro validation logic."""

import re
from typing import Set

from macros.domain.model.macro import Macro, LlmStep
from macros.domain.exceptions import MacroValidationError


STEP_OUTPUT_PATTERN = re.compile(r"\{\{STEP_OUTPUT:([^}]+)\}\}")


class MacroValidator:
    """Validates macro definitions beyond schema validation.
    
    Performs domain-level validation:
    - Step IDs must be unique
    - STEP_OUTPUT references must point to earlier steps
    - At least one step required
    """

    def validate(self, macro: Macro) -> None:
        """Validate a macro definition.
        
        Raises:
            MacroValidationError: If validation fails
        """
        self._validate_has_steps(macro)
        self._validate_unique_step_ids(macro)
        self._validate_step_references(macro)

    def _validate_has_steps(self, macro: Macro) -> None:
        if not macro.steps:
            raise MacroValidationError(
                f"Macro '{macro.macro_id}' must have at least one step"
            )

    def _validate_unique_step_ids(self, macro: Macro) -> None:
        seen: Set[str] = set()
        for step in macro.steps:
            if step.id in seen:
                raise MacroValidationError(
                    f"Duplicate step ID '{step.id}' in macro '{macro.macro_id}'"
                )
            seen.add(step.id)

    def _validate_step_references(self, macro: Macro) -> None:
        """Ensure STEP_OUTPUT references point to earlier steps."""
        seen_ids: Set[str] = set()
        
        for step in macro.steps:
            if isinstance(step, LlmStep):
                referenced_ids = self._extract_step_references(step.prompt)
                
                for ref_id in referenced_ids:
                    if ref_id not in seen_ids:
                        raise MacroValidationError(
                            f"Step '{step.id}' references unknown or future step '{ref_id}'. "
                            f"Steps can only reference earlier steps."
                        )
            
            seen_ids.add(step.id)

    def _extract_step_references(self, prompt: str) -> Set[str]:
        matches = STEP_OUTPUT_PATTERN.findall(prompt)
        return set(matches)
