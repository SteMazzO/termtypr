"""Tests for user preferences model."""

import pytest
from pydantic import ValidationError

from termtypr.domain.models.user_preferences import GhostSaveMode, UserPreferences


def test_word_count_lower_bound():
    """Test that word count below 5 is rejected."""
    with pytest.raises(ValidationError):
        UserPreferences(word_count=2)


def test_word_count_upper_bound():
    """Test that word count above 200 is rejected."""
    with pytest.raises(ValidationError):
        UserPreferences(word_count=300)


def test_serialization():
    """Test JSON round-trip."""
    prefs = UserPreferences(word_count=75)
    json_str = prefs.model_dump_json()
    restored = UserPreferences.model_validate_json(json_str)
    assert restored.word_count == 75


def test_ghost_defaults():
    """Ghost settings have sensible defaults."""
    prefs = UserPreferences()
    assert prefs.ghost_save_mode is GhostSaveMode.AUTO_BEST
    assert prefs.ghost_wpm_threshold == 60.0
    assert prefs.ghost_min_accuracy == 85.0
    assert prefs.max_ghosts_total == 100


def test_ghost_save_mode_coerced_from_string():
    """Persisted mode strings load back as the enum."""
    prefs = UserPreferences(ghost_save_mode="threshold")
    assert prefs.ghost_save_mode is GhostSaveMode.AUTO_THRESHOLD


def test_ghost_settings_round_trip():
    """Ghost settings survive a JSON round-trip."""
    prefs = UserPreferences(
        ghost_save_mode=GhostSaveMode.ALWAYS_ASK,
        ghost_wpm_threshold=72.5,
        ghost_min_accuracy=90.0,
        max_ghosts_total=50,
    )
    restored = UserPreferences.model_validate_json(prefs.model_dump_json())
    assert restored.ghost_save_mode is GhostSaveMode.ALWAYS_ASK
    assert restored.ghost_wpm_threshold == 72.5
    assert restored.ghost_min_accuracy == 90.0
    assert restored.max_ghosts_total == 50


@pytest.mark.parametrize(
    "field, value",
    [
        ("ghost_wpm_threshold", -1.0),
        ("ghost_wpm_threshold", 1000.0),
        ("ghost_min_accuracy", -5.0),
        ("ghost_min_accuracy", 101.0),
        ("max_ghosts_total", 0),
        ("max_ghosts_total", 100000),
    ],
)
def test_ghost_settings_bounds(field, value):
    """Out-of-range ghost settings are rejected."""
    with pytest.raises(ValidationError):
        UserPreferences(**{field: value})
