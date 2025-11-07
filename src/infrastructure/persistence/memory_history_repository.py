"""In-memory implementation of history repository for testing."""

from typing import Optional

from src.domain.models.game_result import GameResult
from src.domain.repositories.history_repository import HistoryRepository


class InMemoryHistoryRepository(HistoryRepository):
    """In-memory repository for testing without file I/O."""

    def __init__(self):
        """Initialize empty in-memory storage."""
        self._results: list[GameResult] = []

    def save(self, result: GameResult) -> bool:
        """Save a game result to memory."""
        self._results.append(result)
        return True

    def get_all(self) -> list[GameResult]:
        """Get all game results from memory."""
        # Return copy, newest first
        return list(reversed(self._results))

    def get_best(self) -> Optional[GameResult]:
        """Get the best game result based on WPM."""
        if not self._results:
            return None
        return max(self._results, key=lambda r: r.wpm)

    def get_recent(self, limit: int = 10) -> list[GameResult]:
        """Get recent game results."""
        return self.get_all()[:limit]

    def clear(self) -> bool:
        """Clear all history."""
        self._results.clear()
        return True
