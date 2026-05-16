"""Pipeline runner — Sprint 2.

Drives an :class:`OriginAdapter` through a declared list of entity types,
writing each emitted row into a :class:`DpmfWriter`, optionally consulting
a :class:`CheckpointStore` to skip rows that were already emitted in a
prior, interrupted run.
"""

from __future__ import annotations

from dataclasses import dataclass

from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
)

from dental_bridge.core.adapters.origin_abc import OriginAdapter
from dental_bridge.core.dpmf.writer import DpmfWriter
from dental_bridge.core.pipeline.checkpoint import CheckpointStore
from dental_bridge.core.pipeline.errors import WarningRegistry
from dental_bridge.core.pipeline.id_mapping import IdMapping
from dental_bridge.core.pipeline.self_fk import validate_and_nullify_orphans


@dataclass(slots=True)
class RunSummary:
    rows_by_entity: dict[str, int]
    warnings: WarningRegistry


def run_extraction(
    adapter: OriginAdapter,
    writer: DpmfWriter,
    entity_order: list[str],
    *,
    id_mapping: IdMapping | None = None,
    warnings: WarningRegistry | None = None,
    checkpoint: CheckpointStore | None = None,
    run_id: str | None = None,
    show_progress: bool = True,
) -> RunSummary:
    """Extract the given entity types from ``adapter`` into ``writer``.

    ``entity_order`` must satisfy any referential dependencies between the
    listed entities — for v0.1 the caller hands us the order; the runner
    does not introspect dependencies.

    When ``checkpoint`` is provided the runner skips rows that have
    already been emitted in a prior, interrupted invocation of the same
    ``run_id``. The skipped rows still count toward the per-entity total
    so on-screen counters reflect what is in the DPMF file, not just what
    this invocation wrote.
    """
    if checkpoint is not None and run_id is None:
        raise ValueError("run_id is required when a checkpoint store is provided")
    id_mapping = id_mapping if id_mapping is not None else IdMapping()
    warnings = warnings if warnings is not None else WarningRegistry()
    rows: dict[str, int] = dict.fromkeys(entity_order, 0)

    progress_ctx = (
        Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("{task.completed} rows"),
            TimeElapsedColumn(),
        )
        if show_progress
        else _NullProgress()
    )

    with progress_ctx as progress:
        for entity_type in entity_order:
            task_id = progress.add_task(f"Extracting {entity_type}", total=None)
            for entity in adapter.iter_entity(entity_type):
                if checkpoint is not None and checkpoint.is_emitted(
                    run_id, entity.entity_type, entity.source_id
                ):
                    rows[entity_type] += 1
                    progress.update(task_id, advance=1)
                    continue
                writer.append(entity)
                if checkpoint is not None:
                    checkpoint.mark_emitted(run_id, entity.entity_type, entity.source_id)
                rows[entity_type] += 1
                progress.update(task_id, advance=1)
            progress.update(
                task_id,
                description=f"[green]{entity_type} done[/green]",
                total=rows[entity_type],
                completed=rows[entity_type],
            )

    for entity_type, count in rows.items():
        writer.record_entity_count(entity_type, count)

    # Self-FK validation — runs after every entity has been emitted so the
    # set of "known canonical UUIDs" is complete.
    validate_and_nullify_orphans(writer.connection, warnings)

    for warning in warnings:
        writer.append_warning(warning)

    return RunSummary(rows_by_entity=rows, warnings=warnings)


class _NullProgress:
    """No-op context manager mirroring the bits of `rich.progress.Progress` we use."""

    def __enter__(self) -> _NullProgress:
        return self

    def __exit__(self, *exc: object) -> None:
        return None

    def add_task(self, *_args: object, **_kwargs: object) -> int:
        return 0

    def update(self, *_args: object, **_kwargs: object) -> None:
        return None
