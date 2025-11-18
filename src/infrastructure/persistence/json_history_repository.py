"""JSON file-based implementation of history repository."""

import json
import os
from typing import Optional

import platformdirs

from src.domain.models.game_result import GameResult
from src.domain.repositories.history_repository import HistoryRepository


class JsonHistoryRepository(HistoryRepository):
    """JSON file-based repository for typing test history."""

    def __init__(self, file_path: Optional[str] = None):
        """Initialize the repository.

        Args:
            file_path: Path to JSON file. If None, uses default location.
        """
        if file_path:
            self.file_path = file_path
        else:
            data_dir = platformdirs.user_data_dir("termtypr")
            os.makedirs(data_dir, exist_ok=True)
            self.file_path = os.path.join(data_dir, "history.json")

        # Initialize file if it doesn't exist
        if not os.path.exists(self.file_path):
            self._initialize_file()

    def _initialize_file(self) -> None:
        """Create an empty history file."""
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump({"history": []}, f)

    def _load_data(self) -> dict:
        """Load data from JSON file."""
        try:
            with open(self.file_path, encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {"history": []}

    def _save_data(self, data: dict) -> bool:
        """Save data to JSON file."""
        try:
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving history: {e}")
            return False

    def save(self, result: GameResult) -> bool:
        """Save a game result to history."""
        data = self._load_data()
        history = data.get("history", [])

        # Add new result
        history.append(result.to_dict())

        # Save back
        data["history"] = history
        return self._save_data(data)

    def get_all(self, sort: str = "desc") -> list[GameResult]:
        """Get all game results from history.

        Args:
            sort: Sort order - 'desc' for newest first (default), 'asc' for oldest first
        """
        data = self._load_data()
        history = data.get("history", [])

        # Convert to GameResult objects
        results = []
        for record in history:
            try:
                results.append(GameResult.from_dict(record))
            except Exception as e:
                print(f"Error parsing record: {e}")
                continue

        # Sort by timestamp
        results.sort(key=lambda r: r.timestamp, reverse=(sort == "desc"))
        return results

    def get_best(self) -> Optional[GameResult]:
        """Get the best game result based on WPM."""
        results = self.get_all()
        if not results:
            return None

        return max(results, key=lambda r: r.wpm)

    def get_recent(self, limit: int = 10, sort: str = "desc") -> list[GameResult]:
        """Get recent game results.

        Args:
            limit: Maximum number of results to return
            sort: Sort order - 'desc' for newest first (default), 'asc' for oldest first
        """
        results = self.get_all(sort=sort)
        return results[:limit]

    def clear(self) -> bool:
        """Clear all history."""
        return self._save_data({"history": []})
