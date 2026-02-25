"""Tests for JSON preferences repository."""

import json

import pytest

from termtypr.domain.models.user_preferences import UserPreferences
from termtypr.infrastructure.persistence.json_preferences_repository import (
    JsonPreferencesRepository,
)


@pytest.fixture()
def prefs_file(tmp_path):
    """Return a temporary preferences file path."""
    return tmp_path / "preferences.json"


def test_load_returns_defaults_when_file_missing(prefs_file):
    """Loading from a non-existent file returns default preferences."""
    repo = JsonPreferencesRepository(prefs_file)
    prefs = repo.load()
    assert prefs.word_count == 20


def test_save_and_load_round_trip(prefs_file):
    """Saved preferences can be loaded back."""
    repo = JsonPreferencesRepository(prefs_file)

    prefs = UserPreferences(word_count=50)
    repo.save(prefs)

    loaded = repo.load()
    assert loaded.word_count == 50


def test_load_returns_defaults_on_corrupt_json(prefs_file):
    """Corrupt JSON falls back to defaults."""
    prefs_file.write_text("not json at all", encoding="utf-8")

    repo = JsonPreferencesRepository(prefs_file)
    prefs = repo.load()
    assert prefs.word_count == 20


def test_load_returns_defaults_on_invalid_values(prefs_file):
    """JSON with invalid field values falls back to defaults."""
    prefs_file.write_text(json.dumps({"word_count": -5}), encoding="utf-8")

    repo = JsonPreferencesRepository(prefs_file)
    prefs = repo.load()
    assert prefs.word_count == 20


def test_save_creates_parent_directories(tmp_path):
    """Save creates intermediate directories if needed."""
    deep_path = tmp_path / "a" / "b" / "preferences.json"
    repo = JsonPreferencesRepository(deep_path)

    repo.save(UserPreferences(word_count=30))
    loaded = repo.load()
    assert loaded.word_count == 30


def test_overwrite_preserves_latest(prefs_file):
    """Overwriting keeps only the latest values."""
    repo = JsonPreferencesRepository(prefs_file)

    repo.save(UserPreferences(word_count=10))
    repo.save(UserPreferences(word_count=80))

    loaded = repo.load()
    assert loaded.word_count == 80
