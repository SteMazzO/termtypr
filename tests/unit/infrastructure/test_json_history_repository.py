"""Tests for JSON history repository."""

import json
import os
import shutil
import tempfile
from datetime import datetime, timedelta, timezone

import pytest

from termtypr.domain.models.game_result import GameResult
from termtypr.infrastructure.persistence.json_history_repository import (
    JsonHistoryRepository,
)


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
        timestamp=datetime.now(tz=timezone.utc),
    )

    repo.save(result)

    all_results = repo.get_all()
    assert len(all_results) == 1
    assert all_results[0].wpm == 50.0


def test_get_best(temp_file):
    """Test getting best result."""
    repo = JsonHistoryRepository(temp_file)
    base_time = datetime.now(tz=timezone.utc)

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


def test_clear(temp_file):
    """Test clearing history."""
    repo = JsonHistoryRepository(temp_file)

    # Add a result
    result = GameResult(
        wpm=50.0,
        accuracy=95.0,
        duration=60.0,
        game_type="Random Words",
        timestamp=datetime.now(tz=timezone.utc),
    )
    repo.save(result)

    # Clear
    repo.clear()

    # Should be empty
    assert len(repo.get_all()) == 0


def test_empty_repository(temp_file):
    """Test behavior with empty repository."""
    repo = JsonHistoryRepository(temp_file)

    assert len(repo.get_all()) == 0
    assert repo.get_best() is None


def test_save_recreates_deleted_data_directory(tmp_path):
    """Saving still works if the data directory vanished after init."""
    file_path = tmp_path / "data" / "history.json"
    repo = JsonHistoryRepository(file_path)
    shutil.rmtree(file_path.parent)

    repo.save(
        GameResult(
            wpm=50.0,
            accuracy=95.0,
            duration=60.0,
            game_type="Random Words",
            timestamp=datetime.now(tz=timezone.utc),
        )
    )

    assert file_path.exists()
    assert len(repo.get_all()) == 1


def test_corrupt_records_are_skipped(temp_file):
    """Unparseable history records are dropped; valid ones still load."""
    with open(temp_file, "w", encoding="utf-8") as f:
        json.dump(
            {
                "history": [
                    {
                        "wpm": 50.0,
                        "accuracy": 95.0,
                        "duration": 60.0,
                        "game_type": "Random Words",
                        "timestamp": "2026-01-15T12:00:00+00:00",
                    },
                    {"timestamp": 12345},  # non-string timestamp
                    "not even a dict",
                    {"timestamp": "not-a-date"},
                ]
            },
            f,
        )

    repo = JsonHistoryRepository(temp_file)

    results = repo.get_all()
    assert len(results) == 1
    assert results[0].wpm == 50.0


def test_corrupt_file_treated_as_empty(temp_file):
    """A history file with invalid JSON loads as empty history."""
    with open(temp_file, "w", encoding="utf-8") as f:
        f.write("{broken json")

    repo = JsonHistoryRepository(temp_file)

    assert repo.get_all() == []
    assert repo.get_best() is None


def test_multiple_saves(temp_file):
    """Test saving multiple results."""
    repo = JsonHistoryRepository(temp_file)
    base_time = datetime.now(tz=timezone.utc)

    for i in range(5):
        result = GameResult(
            wpm=float(i * 10),
            accuracy=95.0,
            duration=60.0,
            game_type="Random Words",
            timestamp=base_time + timedelta(seconds=i),
        )
        repo.save(result)

    all_results = repo.get_all()
    assert len(all_results) == 5
    # Verify newest first
    assert all_results[0].wpm == 40.0
    assert all_results[4].wpm == 0.0
