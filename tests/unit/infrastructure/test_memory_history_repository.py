"""Tests for in-memory history repository."""

from datetime import datetime, timedelta

import pytest

from src.domain.models.game_result import GameResult
from src.infrastructure.persistence.memory_history_repository import (
    InMemoryHistoryRepository,
)


@pytest.fixture
def repo():
    """Create fresh in-memory repository for each test."""
    return InMemoryHistoryRepository()


def test_save_and_get_all(repo):
    """Test saving and retrieving results."""
    result = GameResult(
        wpm=50.0,
        accuracy=95.0,
        duration=60.0,
        game_type="Random Words",
        timestamp=datetime.now(),
    )

    assert repo.save(result)

    all_results = repo.get_all()
    assert len(all_results) == 1
    assert all_results[0].wpm == 50.0


def test_get_best(repo):
    """Test getting best result."""
    # Add multiple results
    for wpm in [40.0, 60.0, 50.0]:
        result = GameResult(
            wpm=wpm,
            accuracy=95.0,
            duration=60.0,
            game_type="Random Words",
            timestamp=datetime.now(),
        )
        repo.save(result)

    best = repo.get_best()
    assert best is not None
    assert best.wpm == 60.0


def test_get_recent(repo):
    """Test getting recent results."""
    base_time = datetime.now()
    # Add 15 results
    for i in range(15):
        result = GameResult(
            wpm=float(i),
            accuracy=95.0,
            duration=60.0,
            game_type="Random Words",
            timestamp=base_time + timedelta(seconds=i),
        )
        repo.save(result)

    recent = repo.get_recent(limit=10)
    assert len(recent) == 10
    # Should be newest first
    assert recent[0].wpm == 14.0


def test_clear(repo):
    """Test clearing history."""
    # Add a result
    result = GameResult(
        wpm=50.0,
        accuracy=95.0,
        duration=60.0,
        game_type="Random Words",
        timestamp=datetime.now(),
    )
    repo.save(result)

    # Clear
    assert repo.clear()

    # Should be empty
    assert len(repo.get_all()) == 0


def test_empty_repository(repo):
    """Test behavior with empty repository."""
    assert len(repo.get_all()) == 0
    assert repo.get_best() is None
    assert len(repo.get_recent()) == 0
