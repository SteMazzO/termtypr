"""Tests for TypingStats value object."""

import pytest

from src.domain.models.typing_stats import TypingStats


def test_create_valid_stats():
    """Test creating valid typing stats."""
    stats = TypingStats(
        wpm=50.0,
        accuracy=95.0,
        duration=60.0,
        typed_word_count=50,
        target_word_count=50,
        total_characters=250,
        correct_characters=240,
        error_count=10,
        is_completed=True,
    )

    assert stats.wpm == 50.0
    assert stats.accuracy == 95.0
    assert stats.is_completed is True


def test_negative_wpm_raises_error():
    """Test that negative WPM raises ValueError."""
    with pytest.raises(ValueError, match="WPM cannot be negative"):
        TypingStats(
            wpm=-10.0,
            accuracy=95.0,
            duration=60.0,
            typed_word_count=50,
            target_word_count=50,
            total_characters=250,
            correct_characters=240,
            error_count=10,
            is_completed=True,
        )


def test_invalid_accuracy_raises_error():
    """Test that accuracy outside 0-100 raises ValueError."""
    with pytest.raises(ValueError, match="Accuracy must be between 0 and 100"):
        TypingStats(
            wpm=50.0,
            accuracy=150.0,  # Invalid
            duration=60.0,
            typed_word_count=50,
            target_word_count=50,
            total_characters=250,
            correct_characters=240,
            error_count=10,
            is_completed=True,
        )


def test_completion_percentage():
    """Test completion percentage calculation."""
    stats = TypingStats(
        wpm=50.0,
        accuracy=95.0,
        duration=60.0,
        typed_word_count=25,
        target_word_count=50,
        total_characters=125,
        correct_characters=120,
        error_count=5,
        is_completed=False,
    )

    assert stats.completion_percentage == 50.0


def test_errors_per_word():
    """Test errors per word calculation."""
    stats = TypingStats(
        wpm=50.0,
        accuracy=95.0,
        duration=60.0,
        typed_word_count=50,
        target_word_count=50,
        total_characters=250,
        correct_characters=240,
        error_count=10,
        is_completed=True,
    )

    assert stats.errors_per_word == 0.2  # 10 errors / 50 words


def test_characters_per_minute():
    """Test characters per minute calculation."""
    stats = TypingStats(
        wpm=50.0,
        accuracy=95.0,
        duration=60.0,
        typed_word_count=50,
        target_word_count=50,
        total_characters=250,
        correct_characters=240,
        error_count=10,
        is_completed=True,
    )

    # Use approximate comparison for floating point
    assert abs(stats.characters_per_minute - 250.0) < 0.01


def test_to_dict():
    """Test conversion to dictionary."""
    stats = TypingStats(
        wpm=50.0,
        accuracy=95.0,
        duration=60.0,
        typed_word_count=50,
        target_word_count=50,
        total_characters=250,
        correct_characters=240,
        error_count=10,
        is_completed=True,
    )

    data = stats.to_dict()

    assert data["wpm"] == 50.0
    assert data["accuracy"] == 95.0
    assert data["completion_percentage"] == 100.0


def test_from_dict():
    """Test creating from dictionary."""
    data = {
        "wpm": 50.0,
        "accuracy": 95.0,
        "duration": 60.0,
        "typed_word_count": 50,
        "target_word_count": 50,
        "total_characters": 250,
        "correct_characters": 240,
        "error_count": 10,
        "is_completed": True,
    }

    stats = TypingStats.from_dict(data)

    assert stats.wpm == 50.0
    assert stats.accuracy == 95.0
    assert stats.is_completed is True


def test_immutability():
    """Test that TypingStats is immutable."""
    stats = TypingStats(
        wpm=50.0,
        accuracy=95.0,
        duration=60.0,
        typed_word_count=50,
        target_word_count=50,
        total_characters=250,
        correct_characters=240,
        error_count=10,
        is_completed=True,
    )

    with pytest.raises(AttributeError):
        stats.wpm = 60.0  # Should fail - immutable
