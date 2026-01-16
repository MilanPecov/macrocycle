from macros.domain.model.cycle import Cycle
from macros.domain.services.cycle_orchestrator import CycleOrchestrator
from macros.application.container import Container


def run_macro(
    container: Container,
    macro_id: str,
    input_text: str,
    *,
    yes: bool,
    until: str | None,
) -> Cycle:
    """Execute a macro and return the cycle."""
    macro = container.macro_registry.load_macro(macro_id)

    orchestrator = CycleOrchestrator(
        agent=container.agent,
        cycle_store=container.cycle_store,
        console=container.console,
    )

    return orchestrator.run(
        macro=macro,
        input_text=input_text,
        auto_approve=yes,
        stop_after=until,
    )
