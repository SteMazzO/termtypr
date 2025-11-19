"""Tests for JSON history repository."""

import os
import tempfile
from datetime import datetime, timedelta

import pytest

from src.domain.models.game_result import GameResult
from src.infrastructure.persistence.json_history_repository import JsonHistoryRepository


@pytest.fixture
def temp_file():
    """Create temporary file for testing."""
    fd, path = tempfile.mkstemp(suffix=".json")
    os.close(fd)
    yield path
    if os.path.exists(path):
        os.unlink(path)


def test_save_and_get_all(temp_file):
    """Test saving and retrieving results."""
    repo = JsonHistoryRepository(temp_file)

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


def test_get_best(temp_file):
    """Test getting best result."""
    repo = JsonHistoryRepository(temp_file)
    base_time = datetime.now()

    # Add multiple results
    for i, wpm in enumerate([40.0, 60.0, 50.0]):
        result = GameResult(
            wpm=wpm,
            accuracy=95.0,
            duration=60.0,
            game_type="Random Words",
            timestamp=base_time + timedelta(seconds=i),
        )
        repo.save(result)

    best = repo.get_best()
    assert best is not None
    assert best.wpm == 60.0


def test_get_recent(temp_file):
    """Test getting recent results."""
    repo = JsonHistoryRepository(temp_file)
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


def test_clear(temp_file):
    """Test clearing history."""
    repo = JsonHistoryRepository(temp_file)

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


def test_empty_repository(temp_file):
    """Test behavior with empty repository."""
    repo = JsonHistoryRepository(temp_file)

    assert len(repo.get_all()) == 0
    assert repo.get_best() is None
    assert len(repo.get_recent()) == 0


def test_multiple_saves(temp_file):
    """Test saving multiple results."""
    repo = JsonHistoryRepository(temp_file)
    base_time = datetime.now()

    for i in range(5):
        result = GameResult(
            wpm=float(i * 10),
            accuracy=95.0,
            duration=60.0,
            game_type="Random Words",
            timestamp=base_time + timedelta(seconds=i),
        )
        assert repo.save(result)

    all_results = repo.get_all()
    assert len(all_results) == 5
    # Verify newest first
    assert all_results[0].wpm == 40.0
    assert all_results[4].wpm == 0.0
