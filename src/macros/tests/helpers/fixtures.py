"""Shared test fixtures and constants."""

import json
from pathlib import Path

from macros.infrastructure.runtime.utils.workspace import set_workspace


# =============================================================================
# Test Macro Definitions
# =============================================================================

SAMPLE_MACRO_DICT = {
    "macro_id": "sample",
    "name": "Sample Macro",
    "engine": "cursor",
    "include_previous_outputs": True,
    "steps": [
        {"id": "s1", "type": "llm", "prompt": "Do something with {{INPUT}}"},
        {"id": "g1", "type": "gate", "message": "Continue?"},
        {"id": "s2", "type": "llm", "prompt": "Based on: {{STEP_OUTPUT:s1}}"},
    ]
}

SAMPLE_MACRO_JSON = json.dumps(SAMPLE_MACRO_DICT)

# A comprehensive macro covering many domain cases
E2E_TEST_MACRO = {
    "macro_id": "test_flow",
    "name": "Test Flow",
    "engine": "cursor",
    "include_previous_outputs": True,
    "steps": [
        # Step 1: Tests {{INPUT}} substitution
        {"id": "analyze", "type": "llm", "prompt": "Analyze: {{INPUT}}"},
        # Step 2: Tests context accumulation (previous output appended)
        {"id": "plan", "type": "llm", "prompt": "Create plan based on analysis."},
        # Step 3: Gate after LLM steps
        {"id": "approve", "type": "gate", "message": "Approve plan?"},
        # Step 4: LLM after gate, explicit {{STEP_OUTPUT:id}} reference
        {"id": "implement", "type": "llm", "prompt": "Implement: {{STEP_OUTPUT:plan}}"},
        # Step 5: Multiple gates in flow
        {"id": "review", "type": "gate", "message": "Review complete?"},
        # Step 6: Reference non-adjacent step
        {"id": "finalize", "type": "llm", "prompt": "Finalize. Original was: {{STEP_OUTPUT:analyze}}"},
    ]
}


# =============================================================================
# Workspace Helpers
# =============================================================================

def init_test_workspace(path: Path) -> None:
    """Initialize a test workspace with .git marker.
    
    GIVEN: A path to use as workspace
    WHEN:  Called
    THEN:  Creates .git dir and sets workspace
    """
    Path(path / ".git").mkdir(parents=True, exist_ok=True)
    set_workspace(path)


def write_macro_to_workspace(workspace: Path, macro: dict) -> None:
    """Write a macro definition to the workspace.
    
    GIVEN: A workspace path and macro dict
    WHEN:  Called
    THEN:  Writes the macro JSON to .macrocycle/macros/<macro_id>.json
    """
    macro_dir = workspace / ".macrocycle" / "macros"
    macro_dir.mkdir(parents=True, exist_ok=True)
    (macro_dir / f"{macro['macro_id']}.json").write_text(json.dumps(macro))


def init_cycles_dir(workspace: Path) -> None:
    """Create the cycles directory in the workspace."""
    (workspace / ".macrocycle" / "cycles").mkdir(parents=True, exist_ok=True)
