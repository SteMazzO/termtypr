"""Abstract repository interface for typing test history."""

from abc import ABC, abstractmethod
from typing import Optional


class HistoryRepository(ABC):
    """Abstract repository for managing typing test history."""

    @abstractmethod
    def save(self, result: "GameResult") -> bool:
        """Save a game result to history.

        Args:
            result: The game result to save

        Returns:
            True if successful, False otherwise
        """

    @abstractmethod
    def get_all(self, sort: str = "desc") -> list["GameResult"]:
        """Get all game results from history.

        Args:
            sort: Sort order - 'desc' for newest first (default), 'asc' for oldest first

        Returns:
            List of all game results, sorted by timestamp
        """

    @abstractmethod
    def get_best(self) -> Optional["GameResult"]:
        """Get the best game result based on WPM.

        Returns:
            Best game result or None if no history exists
        """

    @abstractmethod
    def get_recent(self, limit: int = 10, sort: str = "desc") -> list["GameResult"]:
        """Get recent game results.

        Args:
            limit: Maximum number of results to return
            sort: Sort order - 'desc' for newest first (default), 'asc' for oldest first

        Returns:
            List of recent game results
        """

    @abstractmethod
    def clear(self) -> bool:
        """Clear all history.

        Returns:
            True if successful, False otherwise
        """
