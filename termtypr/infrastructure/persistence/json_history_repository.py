"""JSON file-based implementation of history repository."""

import json
import logging
import os
from pathlib import Path
from typing import Literal

from termtypr.config import RECORDS_FILE
from termtypr.domain.history_repository import HistoryRepository
from termtypr.domain.models.game_result import GameResult

logger = logging.getLogger(__name__)


class JsonHistoryRepository(HistoryRepository):
    """JSON file-based repository for typing test history."""

    def __init__(self, file_path: str | Path | None = None):
        """Initialize the repository.

        Args:
            file_path: Path to JSON file. If None, uses RECORDS_FILE from config.
        """
        self.file_path = Path(file_path) if file_path else RECORDS_FILE
        self._results_cache: list[GameResult] | None = None

        # Initialize file if it doesn't exist
        if not self.file_path.exists():
            self._initialize_file()

    def _invalidate_cache(self) -> None:
        """Invalidate the in-memory results cache."""
        self._results_cache = None

    def _initialize_file(self) -> None:
        """Create an empty history file."""
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump({"history": []}, f)

    def _load_data(self) -> dict:
        """Load raw data from JSON file."""
        try:
            with open(self.file_path, encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {"history": []}

    def _save_data(self, data: dict) -> None:
        """Save data to JSON file atomically.

        Writing to a temp file first prevents a crash mid-write from
        corrupting (and thereby silently wiping) the whole history.
        """
        tmp_path = self.file_path.with_suffix(".json.tmp")
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        os.replace(tmp_path, self.file_path)

    @staticmethod
    def _parse_record(record: dict) -> GameResult | None:
        """Parse a single history record, returning None if it is corrupt."""
        try:
            return GameResult.from_dict(record)
        except (ValueError, TypeError, AttributeError) as exc:
            logger.warning("Skipping corrupt history record %r: %s", record, exc)
            return None

    def _load_results(self) -> list[GameResult]:
        """Load and cache parsed GameResult objects (unsorted).

        Corrupt records are skipped (with a warning) instead of crashing.
        """
        if self._results_cache is not None:
            return self._results_cache

        history = self._load_data().get("history", [])
        parsed = (self._parse_record(record) for record in history)
        self._results_cache = [result for result in parsed if result is not None]
        return self._results_cache

    def save(self, result: GameResult) -> None:
        """Save a game result to history."""
        data = self._load_data()
        history = data.get("history", [])

        # Add new result
        history.append(result.to_dict())

        # Save back
        data["history"] = history
        self._save_data(data)

        if self._results_cache is not None:
            self._results_cache.append(result)

    def get_all(self, sort: Literal["asc", "desc"] = "desc") -> list[GameResult]:
        """Get all game results from history.

        Args:
            sort: Sort order - 'desc' for newest first (default), 'asc' for oldest first
        """
        results = list(self._load_results())

        # Sort by timestamp
        results.sort(key=lambda r: r.timestamp, reverse=sort == "desc")
        return results

    def get_best(self) -> GameResult | None:
        """Get the best game result based on WPM."""
        results = self._load_results()
        if not results:
            return None

        return max(results, key=lambda r: r.wpm)

    def clear(self) -> None:
        """Clear all history."""
        self._save_data({"history": []})
        self._invalidate_cache()
