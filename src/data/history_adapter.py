"""Adapter to maintain backward compatibility with existing HistoryManager API."""

from datetime import datetime
from typing import Optional

from src.domain.models.game_result import GameResult
from src.domain.repositories.history_repository import HistoryRepository
from src.infrastructure.persistence.json_history_repository import JsonHistoryRepository


class HistoryManager:
    """Adapter class that wraps the new repository pattern.

    This maintains backward compatibility, eventually this class will be removed.
    """

    def __init__(self, history_file: Optional[str] = None):
        """Initialize with repository."""
        self._repository: HistoryRepository = JsonHistoryRepository(history_file)

    def get_history(self) -> list[dict]:
        """Get all typing history (backward compatible)."""
        results = self._repository.get_all()
        return [r.to_dict() for r in results]

    def add_to_history(
        self, wpm: float, accuracy: float, duration: float, game: str
    ) -> bool:
        """Add a new typing test to history."""
        result = GameResult(
            wpm=wpm,
            accuracy=accuracy,
            duration=duration,
            game_type=game,
            timestamp=datetime.now(),
        )
        return self._repository.save(result)

    def get_best_record(self) -> dict:
        """Get the best typing test record."""
        best = self._repository.get_best()
        return best.to_dict() if best else {}

    # New methods that expose repository
    def get_repository(self) -> HistoryRepository:
        """Get the underlying repository."""
        return self._repository
