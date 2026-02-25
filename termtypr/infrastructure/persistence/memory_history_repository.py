"""In-memory implementation of history repository for testing."""

from typing import Literal

from termtypr.domain.history_repository import HistoryRepository
from termtypr.domain.models.game_result import GameResult


class InMemoryHistoryRepository(HistoryRepository):
    """In-memory repository for testing without file I/O."""

    def __init__(self):
        """Initialize empty in-memory storage."""
        self._results: list[GameResult] = []

    def save(self, result: GameResult) -> None:
        """Save a game result to memory."""
        self._results.append(result)

    def get_all(self, sort: Literal["asc", "desc"] = "desc") -> list[GameResult]:
        """Get all game results from memory.

        Args:
            sort: Sort order - 'desc' for newest first (default), 'asc' for oldest first
        """
        # Sort by timestamp
        return sorted(
            self._results, key=lambda r: r.timestamp, reverse=(sort == "desc")
        )

    def get_best(self) -> GameResult | None:
        """Get the best game result based on WPM."""
        if not self._results:
            return None
        return max(self._results, key=lambda r: r.wpm)

    def clear(self) -> None:
        """Clear all history."""
        self._results.clear()
