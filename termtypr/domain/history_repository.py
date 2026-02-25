"""Abstract repository interface for typing test history."""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from termtypr.domain.models.game_result import GameResult


class HistoryRepository(ABC):
    """Abstract repository for managing typing test history."""

    @abstractmethod
    def save(self, result: "GameResult") -> None:
        """Save a game result to history.

        Args:
            result: The game result to save
        """

    @abstractmethod
    def get_all(self, sort: Literal["asc", "desc"] = "desc") -> list["GameResult"]:
        """Get all game results from history.

        Args:
            sort: Sort order - 'desc' for newest first (default), 'asc' for oldest first

        Returns:
            List of all game results, sorted by timestamp
        """

    @abstractmethod
    def get_best(self) -> "GameResult | None":
        """Get the best game result based on WPM.

        Returns:
            Best game result or None if no history exists
        """

    @abstractmethod
    def clear(self) -> None:
        """Clear all history."""
