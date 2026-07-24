"""Tests for ghost run domain models."""

from datetime import datetime, timezone

from termtypr.core.phrase_hash import phrase_hash
from termtypr.domain.models.ghost_run import GhostRun, RaceOutcome, RecordingEvent


def make_ghost(duration: float = 12.0) -> GhostRun:
    """Build a small ghost run for tests."""
    return GhostRun(
        phrase_text="hi there",
        wpm=60.0,
        accuracy=95.0,
        duration=duration,
        recording=(RecordingEvent(t=0, w=0, v="h"),),
        timestamp=datetime.now(tz=timezone.utc),
    )


def test_phrase_hash_derived_from_text():
    """A ghost's phrase hash matches the shared hash function."""
    assert make_ghost().phrase_hash == phrase_hash("hi there")


def test_score_is_wpm_times_accuracy():
    """Retention score multiplies WPM by accuracy."""
    assert make_ghost().score == 60.0 * 95.0


def test_race_outcome_won():
    """The player wins by finishing before the ghost."""
    outcome = RaceOutcome(ghost=make_ghost(duration=12.0), player_duration=10.5)

    assert outcome.won is True
    assert outcome.delta_seconds == -1.5


def test_race_outcome_lost():
    """The ghost wins when the player is slower."""
    outcome = RaceOutcome(ghost=make_ghost(duration=12.0), player_duration=14.0)

    assert outcome.won is False
    assert outcome.delta_seconds == 2.0
