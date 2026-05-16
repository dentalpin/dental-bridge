"""Abstract base for origin adapters.

A concrete adapter exposes the entities it can extract and yields canonical
rows for each. The pipeline runner is responsible for ordering, checkpointing
and writing to the DPMF container — adapters only know how to read their
source.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterator
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from dental_bridge.core.canonical.base import BaseCanonicalEntity


class OriginAdapter(ABC):
    """Contract that every origin connector must implement."""

    name: str
    version: str

    @abstractmethod
    def connect(self, dsn: str, **kwargs: object) -> None:
        """Establish a connection to the source system."""

    @abstractmethod
    def fingerprint(self) -> str:
        """Return a stable hash describing the source schema variant.

        Used to detect that the adapter supports the database it was pointed at.
        """

    @abstractmethod
    def supported_entities(self) -> list[str]:
        """List the canonical entity types this adapter can produce."""

    @abstractmethod
    def default_entity_order(self) -> list[str]:
        """Return the topological extraction order for this adapter.

        The order MUST satisfy referential dependencies between the
        emitted entities. The pipeline runner uses this when the caller
        does not pin a custom subset.
        """

    @abstractmethod
    def iter_entity(self, entity_type: str) -> Iterator[BaseCanonicalEntity]:
        """Yield canonical rows for the requested entity type, in extraction order."""

    @abstractmethod
    def close(self) -> None:
        """Release any resources held by the adapter."""
