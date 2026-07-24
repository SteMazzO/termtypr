"""SQLite bootstrap: connection setup, pragmas, and schema creation."""

import sqlite3
from pathlib import Path

SCHEMA_VERSION = 1

_SCHEMA = """
CREATE TABLE IF NOT EXISTS game_history (
    id INTEGER PRIMARY KEY,
    game_type TEXT NOT NULL,
    phrase_text TEXT,
    wpm REAL NOT NULL,
    raw_wpm REAL NOT NULL DEFAULT 0,
    accuracy REAL NOT NULL,
    duration REAL NOT NULL,
    error_count INTEGER NOT NULL DEFAULT 0,
    total_chars INTEGER NOT NULL DEFAULT 0,
    correct_chars INTEGER NOT NULL DEFAULT 0,
    timestamp TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_history_timestamp ON game_history(timestamp);
CREATE INDEX IF NOT EXISTS idx_history_wpm ON game_history(wpm);

CREATE TABLE IF NOT EXISTS ghost_runs (
    id INTEGER PRIMARY KEY,
    game_history_id INTEGER,
    phrase_hash TEXT NOT NULL,
    phrase_text TEXT NOT NULL,
    wpm REAL NOT NULL,
    accuracy REAL NOT NULL,
    duration REAL NOT NULL,
    recording TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    FOREIGN KEY (game_history_id) REFERENCES game_history(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_ghost_phrase ON ghost_runs(phrase_hash);
"""


def connect(db_path: str | Path) -> sqlite3.Connection:
    """Open a connection with pragmas applied and the schema in place.

    SQLite does not enforce foreign keys unless the pragma is set on
    every connection, so all database access must go through here.
    """
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")

    if conn.execute("PRAGMA user_version").fetchone()[0] < SCHEMA_VERSION:
        with conn:
            conn.executescript(_SCHEMA)
            conn.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")

    return conn
