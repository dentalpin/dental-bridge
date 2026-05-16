"""Warning and error registry collected during an extraction run."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import Any, Literal

Severity = Literal["info", "warn", "error"]


@dataclass(slots=True)
class WarningRecord:
    """A non-fatal event observed while extracting one row."""

    entity_type: str | None
    source_id: str | None
    severity: Severity
    code: str
    message: str
    raw_data: dict[str, Any] | None = None


@dataclass(slots=True)
class WarningRegistry:
    """Accumulates warnings emitted by extractors and transformers."""

    _items: list[WarningRecord] = field(default_factory=list)

    def add(
        self,
        *,
        severity: Severity,
        code: str,
        message: str,
        entity_type: str | None = None,
        source_id: str | None = None,
        raw_data: dict[str, Any] | None = None,
    ) -> None:
        self._items.append(
            WarningRecord(
                entity_type=entity_type,
                source_id=source_id,
                severity=severity,
                code=code,
                message=message,
                raw_data=raw_data,
            )
        )

    def __iter__(self) -> Iterator[WarningRecord]:
        return iter(self._items)

    def __len__(self) -> int:
        return len(self._items)
