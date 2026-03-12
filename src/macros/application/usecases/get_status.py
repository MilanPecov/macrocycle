"""Use case: get status of the latest run."""

from macros.application.container import Container
from macros.domain.model.run import RunInfo


def get_status(container: Container) -> RunInfo | None:
    return container.run_store.get_latest_run()
