"""Abstract repository interface for ghost runs."""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from termtypr.domain.models.ghost_run import GhostRun


class GhostRepository(ABC):
    """Abstract repository for managing saved ghost runs."""

    @abstractmethod
    def save(self, ghost: "GhostRun") -> int:
        """Save a ghost run, replacing any existing run for the same phrase.

        Args:
            ghost: The ghost run to save

        Returns:
            The identifier of the stored ghost run
        """

    @abstractmethod
    def get_by_phrase_hash(self, phrase_hash: str) -> "GhostRun | None":
        """Get the saved ghost run for a phrase, if any.

        Args:
            phrase_hash: Stable phrase identifier (see core.phrase_hash)
        """

    @abstractmethod
    def get_all(self) -> list["GhostRun"]:
        """Get all saved ghost runs, newest first."""

    @abstractmethod
    def delete(self, ghost_id: int) -> bool:
        """Delete a ghost run by id.

        Returns:
            True when a run was deleted, False when the id was unknown
        """

    @abstractmethod
    def count(self) -> int:
        """Count the saved ghost runs."""

    @abstractmethod
    def prune(self, max_total: int) -> int:
        """Delete the worst-scoring runs until at most max_total remain.

        Returns:
            The number of runs deleted
        """
