"""Tests for SQLite history repository."""

from datetime import datetime, timedelta, timezone

import pytest

from termtypr.domain.models.game_result import GameResult
from termtypr.infrastructure.persistence.sqlite_history_repository import (
    SqliteHistoryRepository,
)


def make_result(wpm: float = 50.0, offset_seconds: int = 0, **kwargs) -> GameResult:
    """Build a GameResult with sensible defaults for tests."""
    defaults = {
        "wpm": wpm,
        "accuracy": 95.0,
        "duration": 60.0,
        "game_type": "Random Words",
        "timestamp": datetime(2026, 1, 15, 12, 0, tzinfo=timezone.utc)
        + timedelta(seconds=offset_seconds),
    }
    defaults.update(kwargs)
    return GameResult(**defaults)


@pytest.fixture
def repo(tmp_path):
    """Create a repository backed by a fresh temp database."""
    repository = SqliteHistoryRepository(db_path=tmp_path / "test.db")
    yield repository
    repository.close()


def test_save_and_get_all(repo):
    """Saved results can be read back."""
    repo.save(make_result(wpm=50.0))

    all_results = repo.get_all()
    assert len(all_results) == 1
    assert all_results[0].wpm == 50.0


def test_save_returns_row_id(repo):
    """save() returns the database id of the inserted row."""
    first = repo.save(make_result())
    second = repo.save(make_result(offset_seconds=1))

    assert first == 1
    assert second == 2


def test_get_all_sorts_by_timestamp(repo):
    """get_all sorts newest first by default, oldest first with 'asc'."""
    for i, wpm in enumerate([40.0, 60.0, 50.0]):
        repo.save(make_result(wpm=wpm, offset_seconds=i))

    newest_first = repo.get_all()
    assert [r.wpm for r in newest_first] == [50.0, 60.0, 40.0]

    oldest_first = repo.get_all(sort="asc")
    assert [r.wpm for r in oldest_first] == [40.0, 60.0, 50.0]


def test_get_best(repo):
    """get_best returns the highest-WPM result."""
    for i, wpm in enumerate([40.0, 60.0, 50.0]):
        repo.save(make_result(wpm=wpm, offset_seconds=i))

    best = repo.get_best()
    assert best is not None
    assert best.wpm == 60.0


def test_clear(repo):
    """Clearing removes all history."""
    repo.save(make_result())
    repo.clear()

    assert repo.get_all() == []


def test_empty_repository(repo):
    """A fresh repository has no results and no best."""
    assert repo.get_all() == []
    assert repo.get_best() is None


def test_full_result_round_trip(repo):
    """All persisted GameResult fields survive a save/load cycle."""
    original = make_result(
        wpm=82.5,
        raw_wpm=90.1,
        accuracy=96.3,
        duration=25.0,
        game_type="Phrase Typing",
        total_characters=150,
        correct_characters=140,
        error_count=5,
        phrase_text="The quick brown fox jumps over the lazy dog",
    )
    repo.save(original)

    restored = repo.get_all()[0]
    assert restored.wpm == original.wpm
    assert restored.raw_wpm == original.raw_wpm
    assert restored.accuracy == original.accuracy
    assert restored.duration == original.duration
    assert restored.game_type == original.game_type
    assert restored.timestamp == original.timestamp
    assert restored.total_characters == original.total_characters
    assert restored.correct_characters == original.correct_characters
    assert restored.error_count == original.error_count
    assert restored.phrase_text == original.phrase_text
    assert restored.phrase_hash == original.phrase_hash


def test_data_persists_across_connections(tmp_path):
    """Results written by one repository instance are visible to the next."""
    db_path = tmp_path / "test.db"

    first = SqliteHistoryRepository(db_path=db_path)
    first.save(make_result(wpm=70.0))
    first.close()

    second = SqliteHistoryRepository(db_path=db_path)
    assert [r.wpm for r in second.get_all()] == [70.0]
    second.close()


def test_creates_missing_data_directory(tmp_path):
    """The database directory is created when it does not exist yet."""
    db_path = tmp_path / "nested" / "dir" / "test.db"

    repo = SqliteHistoryRepository(db_path=db_path)
    repo.save(make_result())

    assert db_path.exists()
    assert len(repo.get_all()) == 1
    repo.close()


def test_corrupt_rows_are_skipped(repo):
    """Unparseable rows are dropped with a warning; valid ones still load."""
    repo.save(make_result(wpm=50.0))
    repo._conn.execute(
        """
        INSERT INTO game_history (
            game_type, wpm, raw_wpm, accuracy, duration, timestamp
        ) VALUES ('Random Words', 99.0, 99.0, 95.0, 60.0, 'not-a-date')
        """
    )
    repo._conn.commit()

    results = repo.get_all()
    assert len(results) == 1
    assert results[0].wpm == 50.0

    best = repo.get_best()
    assert best is not None
    assert best.wpm == 50.0  # the corrupt 99-WPM row is skipped
