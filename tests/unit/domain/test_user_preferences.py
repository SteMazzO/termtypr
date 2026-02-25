"""Tests for user preferences model."""

import pytest
from pydantic import ValidationError

from termtypr.domain.models.user_preferences import UserPreferences


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
