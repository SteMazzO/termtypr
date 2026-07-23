"""SQLite implementation of history repository."""

import logging
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Literal

from termtypr.config import DATABASE_FILE
from termtypr.domain.history_repository import HistoryRepository
from termtypr.domain.models.game_result import GameResult
from termtypr.infrastructure.persistence import database

logger = logging.getLogger(__name__)


class SqliteHistoryRepository(HistoryRepository):
    """SQLite-backed repository for typing test history."""

    def __init__(self, db_path: str | Path | None = None):
        """Initialize the repository.

        Args:
            db_path: Path to the SQLite database. If None, uses
                DATABASE_FILE from config.
        """
        self.db_path = Path(db_path) if db_path else DATABASE_FILE
        self._conn = database.connect(self.db_path)

    @staticmethod
    def _row_to_result(row: sqlite3.Row) -> GameResult | None:
        """Build a GameResult from a game_history row."""
        try:
            return GameResult(
                wpm=row["wpm"],
                raw_wpm=row["raw_wpm"],
                accuracy=row["accuracy"],
                duration=row["duration"],
                game_type=row["game_type"],
                timestamp=datetime.fromisoformat(row["timestamp"]),
                total_characters=row["total_chars"],
                correct_characters=row["correct_chars"],
                error_count=row["error_count"],
                phrase_text=row["phrase_text"],
            )
        except (ValueError, TypeError) as exc:
            logger.warning("Skipping corrupt history row id=%s: %s", row["id"], exc)
            return None

    def save(self, result: GameResult) -> int:
        """Save a game result to history.

        Returns:
            The database id of the inserted history row.
        """
        with self._conn:
            cursor = self._conn.execute(
                """
                INSERT INTO game_history (
                    game_type, phrase_text, wpm, raw_wpm, accuracy, duration,
                    error_count, total_chars, correct_chars, timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    result.game_type,
                    result.phrase_text,
                    result.wpm,
                    result.raw_wpm,
                    result.accuracy,
                    result.duration,
                    result.error_count,
                    result.total_characters,
                    result.correct_characters,
                    result.timestamp.isoformat(),
                ),
            )
            return cursor.lastrowid

    def get_all(self, sort: Literal["asc", "desc"] = "desc") -> list[GameResult]:
        """Get all game results from history.

        Args:
            sort: Sort order - 'desc' for newest first (default), 'asc' for oldest first
        """
        # Timestamps are always stored as UTC ISO-8601 strings, so text
        # ordering is chronological and the timestamp index applies.
        order = "DESC" if sort == "desc" else "ASC"
        rows = self._conn.execute(
            f"SELECT * FROM game_history ORDER BY timestamp {order}"
        ).fetchall()
        results = (self._row_to_result(row) for row in rows)
        return [result for result in results if result is not None]

    def get_best(self) -> GameResult | None:
        """Get the best game result based on WPM."""
        # Lazy cursor: stops at the first row that parses cleanly
        for row in self._conn.execute("SELECT * FROM game_history ORDER BY wpm DESC"):
            result = self._row_to_result(row)
            if result is not None:
                return result
        return None

    def clear(self) -> None:
        """Clear all history."""
        with self._conn:
            self._conn.execute("DELETE FROM game_history")

    def close(self) -> None:
        """Close the underlying database connection."""
        self._conn.close()
