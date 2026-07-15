"""Tests for SQLite ghost repository."""

from datetime import datetime, timedelta, timezone

import pytest

from termtypr.core.phrase_hash import phrase_hash
from termtypr.domain.models.ghost_run import GhostRun, RecordingEvent
from termtypr.infrastructure.persistence.sqlite_ghost_repository import (
    SqliteGhostRepository,
)
from termtypr.infrastructure.persistence.sqlite_history_repository import (
    SqliteHistoryRepository,
)

from .test_sqlite_history_repository import make_result

RECORDING = (
    RecordingEvent(t=0, w=0, v="h"),
    RecordingEvent(t=200, w=0, v="hi", s=True),
)


def make_ghost(
    phrase: str = "hi there",
    wpm: float = 60.0,
    accuracy: float = 95.0,
    offset_seconds: int = 0,
    **kwargs,
) -> GhostRun:
    """Build a GhostRun with sensible defaults for tests."""
    defaults = {
        "phrase_text": phrase,
        "wpm": wpm,
        "accuracy": accuracy,
        "duration": 12.5,
        "recording": RECORDING,
        "timestamp": datetime(2026, 1, 15, 12, 0, tzinfo=timezone.utc)
        + timedelta(seconds=offset_seconds),
    }
    defaults.update(kwargs)
    return GhostRun(**defaults)


@pytest.fixture
def repo(tmp_path):
    """Create a repository backed by a fresh temp database."""
    repository = SqliteGhostRepository(db_path=tmp_path / "test.db")
    yield repository
    repository.close()


def test_save_and_get_by_phrase_hash(repo):
    """A saved ghost can be fetched by its phrase hash."""
    repo.save(make_ghost())

    ghost = repo.get_by_phrase_hash(phrase_hash("hi there"))
    assert ghost is not None
    assert ghost.phrase_text == "hi there"
    assert ghost.wpm == 60.0
    assert ghost.id is not None


def test_get_by_unknown_phrase_returns_none(repo):
    """Fetching a phrase without a ghost returns None."""
    assert repo.get_by_phrase_hash(phrase_hash("nothing here")) is None


def test_recording_round_trip(repo):
    """The full recording, including submit flags, survives persistence."""
    recording = (
        RecordingEvent(t=0, w=0, v="h"),
        RecordingEvent(t=150, w=0, v="hx"),
        RecordingEvent(t=280, w=0, v="hi", s=True),
        RecordingEvent(t=400, w=1, v='w"eird 	chars'),
    )
    repo.save(make_ghost(recording=recording))

    restored = repo.get_by_phrase_hash(phrase_hash("hi there"))
    assert restored.recording == recording


def test_save_replaces_existing_ghost_for_phrase(repo):
    """Each phrase keeps a single ghost; saving again replaces it."""
    repo.save(make_ghost(wpm=50.0))
    repo.save(make_ghost(wpm=70.0, offset_seconds=10))

    assert repo.count() == 1
    ghost = repo.get_by_phrase_hash(phrase_hash("hi there"))
    assert ghost.wpm == 70.0


def test_get_all_newest_first(repo):
    """get_all returns runs for all phrases, newest first."""
    repo.save(make_ghost(phrase="phrase one", offset_seconds=0))
    repo.save(make_ghost(phrase="phrase two", offset_seconds=10))

    ghosts = repo.get_all()
    assert [g.phrase_text for g in ghosts] == ["phrase two", "phrase one"]


def test_get_random(repo):
    """get_random returns a saved run, or None when there are none."""
    assert repo.get_random() is None

    repo.save(make_ghost(phrase="only phrase"))

    ghost = repo.get_random()
    assert ghost is not None
    assert ghost.phrase_text == "only phrase"


def test_delete(repo):
    """Ghosts can be deleted by id; unknown ids report False."""
    ghost_id = repo.save(make_ghost())

    assert repo.delete(ghost_id) is True
    assert repo.count() == 0
    assert repo.delete(ghost_id) is False


def test_prune_removes_worst_scoring(repo):
    """Pruning drops the lowest wpm*accuracy runs beyond the cap."""
    repo.save(make_ghost(phrase="slow", wpm=30.0, accuracy=90.0))
    repo.save(make_ghost(phrase="fast", wpm=90.0, accuracy=95.0))
    repo.save(make_ghost(phrase="sloppy", wpm=80.0, accuracy=30.0))

    deleted = repo.prune(max_total=1)

    assert deleted == 2
    remaining = repo.get_all()
    assert [g.phrase_text for g in remaining] == ["fast"]


def test_prune_under_cap_is_noop(repo):
    """Pruning does nothing while the cap is not exceeded."""
    repo.save(make_ghost())

    assert repo.prune(max_total=5) == 0
    assert repo.count() == 1


def test_history_link_nulled_when_history_cleared(tmp_path):
    """Clearing game history detaches ghosts instead of breaking them."""
    db_path = tmp_path / "test.db"
    history_repo = SqliteHistoryRepository(db_path=db_path)
    ghost_repo = SqliteGhostRepository(db_path=db_path)

    history_id = history_repo.save(make_result(phrase_text="hi there"))
    ghost_repo.save(make_ghost(game_history_id=history_id))

    history_repo.clear()

    ghost = ghost_repo.get_by_phrase_hash(phrase_hash("hi there"))
    assert ghost is not None
    assert ghost.game_history_id is None

    history_repo.close()
    ghost_repo.close()
