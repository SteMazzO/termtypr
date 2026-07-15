"""SQLite implementation of the ghost run repository."""

import json
import sqlite3
from datetime import datetime
from pathlib import Path

from termtypr.config import DATABASE_FILE
from termtypr.domain.ghost_repository import GhostRepository
from termtypr.domain.models.ghost_run import GhostRun, RecordingEvent
from termtypr.infrastructure.persistence import database


def _encode_recording(recording: tuple[RecordingEvent, ...]) -> str:
    """Serialize a recording to a compact JSON array."""
    return json.dumps(
        [
            {"t": e.t, "w": e.w, "v": e.v, **({"s": 1} if e.s else {})}
            for e in recording
        ],
        separators=(",", ":"),
    )


def _decode_recording(raw: str) -> tuple[RecordingEvent, ...]:
    """Parse a recording from its JSON representation."""
    return tuple(
        RecordingEvent(t=e["t"], w=e["w"], v=e["v"], s=bool(e.get("s")))
        for e in json.loads(raw)
    )


class SqliteGhostRepository(GhostRepository):
    """SQLite-backed repository for ghost runs."""

    def __init__(self, db_path: str | Path | None = None):
        """Initialize the repository.

        Args:
            db_path: Path to the SQLite database. If None, uses
                DATABASE_FILE from config.
        """
        self.db_path = Path(db_path) if db_path else DATABASE_FILE
        self._conn = database.connect(self.db_path)

    @staticmethod
    def _row_to_ghost(row: sqlite3.Row) -> GhostRun:
        """Build a GhostRun from a ghost_runs row."""
        return GhostRun(
            id=row["id"],
            game_history_id=row["game_history_id"],
            phrase_text=row["phrase_text"],
            wpm=row["wpm"],
            accuracy=row["accuracy"],
            duration=row["duration"],
            recording=_decode_recording(row["recording"]),
            timestamp=datetime.fromisoformat(row["timestamp"]),
        )

    def save(self, ghost: GhostRun) -> int:
        """Save a ghost run, replacing any existing run for the same phrase.

        Returns:
            The database id of the inserted ghost run.
        """
        with self._conn:
            self._conn.execute(
                "DELETE FROM ghost_runs WHERE phrase_hash = ?", (ghost.phrase_hash,)
            )
            cursor = self._conn.execute(
                """
                INSERT INTO ghost_runs (
                    game_history_id, phrase_hash, phrase_text, wpm, accuracy,
                    duration, recording, timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    ghost.game_history_id,
                    ghost.phrase_hash,
                    ghost.phrase_text,
                    ghost.wpm,
                    ghost.accuracy,
                    ghost.duration,
                    _encode_recording(ghost.recording),
                    ghost.timestamp.isoformat(),
                ),
            )
            return cursor.lastrowid

    def get_by_phrase_hash(self, phrase_hash: str) -> GhostRun | None:
        """Get the saved ghost run for a phrase, if any."""
        row = self._conn.execute(
            "SELECT * FROM ghost_runs WHERE phrase_hash = ?", (phrase_hash,)
        ).fetchone()
        return self._row_to_ghost(row) if row else None

    def get_all(self) -> list[GhostRun]:
        """Get all saved ghost runs, newest first."""
        rows = self._conn.execute(
            "SELECT * FROM ghost_runs ORDER BY timestamp DESC"
        ).fetchall()
        return [self._row_to_ghost(row) for row in rows]

    def delete(self, ghost_id: int) -> bool:
        """Delete a ghost run by id."""
        with self._conn:
            cursor = self._conn.execute(
                "DELETE FROM ghost_runs WHERE id = ?", (ghost_id,)
            )
            return cursor.rowcount > 0

    def count(self) -> int:
        """Count the saved ghost runs."""
        return self._conn.execute("SELECT COUNT(*) FROM ghost_runs").fetchone()[0]

    def prune(self, max_total: int) -> int:
        """Delete the worst-scoring runs until at most max_total remain."""
        excess = self.count() - max_total
        if excess <= 0:
            return 0

        with self._conn:
            cursor = self._conn.execute(
                """
                DELETE FROM ghost_runs WHERE id IN (
                    SELECT id FROM ghost_runs
                    ORDER BY wpm * accuracy ASC
                    LIMIT ?
                )
                """,
                (excess,),
            )
            return cursor.rowcount

    def close(self) -> None:
        """Close the underlying database connection."""
        self._conn.close()
