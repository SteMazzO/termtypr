"""Tests for the ghost replay engine."""

from datetime import datetime, timezone

import pytest

from termtypr.core.ghost_replay import GhostReplay
from termtypr.domain.models.ghost_run import GhostRun, RecordingEvent


@pytest.fixture
def ghost():
    """A ghost run typing 'hi there' with one corrected typo."""
    recording = (
        RecordingEvent(t=0, w=0, v="h"),
        RecordingEvent(t=100, w=0, v="hx"),  # typo
        RecordingEvent(t=200, w=0, v="h"),  # backspace
        RecordingEvent(t=300, w=0, v="hi"),
        RecordingEvent(t=400, w=0, v="hi", s=True),  # space submits word 0
        RecordingEvent(t=500, w=1, v="t"),
        RecordingEvent(t=600, w=1, v="th"),
        RecordingEvent(t=700, w=1, v="the"),
        RecordingEvent(t=800, w=1, v="ther"),
        RecordingEvent(t=900, w=1, v="there", s=True),  # last word completes
    )
    return GhostRun(
        phrase_text="hi there",
        wpm=48.0,
        accuracy=90.0,
        duration=0.9,
        recording=recording,
        timestamp=datetime.now(tz=timezone.utc),
    )


def test_state_before_first_event(ghost):
    """Negative elapsed time shows the untouched initial state."""
    state = GhostReplay(ghost).state_at(-1)

    assert state.word_index == 0
    assert state.current_input == ""
    assert state.typed_words == []
    assert state.finished is False


def test_state_mid_word(ghost):
    """Events up to the elapsed time are applied, later ones are not."""
    state = GhostReplay(ghost).state_at(150)

    assert state.word_index == 0
    assert state.current_input == "hx"
    assert state.typed_words == ["hx"]


def test_backspace_shows_shrunken_input(ghost):
    """A backspace appears as the input value shrinking."""
    state = GhostReplay(ghost).state_at(250)

    assert state.current_input == "h"


def test_submit_advances_word(ghost):
    """A submit event completes its word and clears the input."""
    state = GhostReplay(ghost).state_at(400)

    assert state.word_index == 1
    assert state.current_input == ""
    assert state.typed_words == ["hi"]


def test_finished_after_last_event(ghost):
    """The ghost is finished once every word was submitted."""
    replay = GhostReplay(ghost)

    assert replay.state_at(899).finished is False

    state = replay.state_at(10_000)
    assert state.finished is True
    assert state.word_index == 2
    assert state.typed_words == ["hi", "there"]


def test_replay_is_deterministic(ghost):
    """Queries are pure: revisiting earlier times gives identical states."""
    replay = GhostReplay(ghost)

    later = replay.state_at(700)
    earlier = replay.state_at(150)

    assert earlier == GhostReplay(ghost).state_at(150)
    assert later == GhostReplay(ghost).state_at(700)


def test_display_data_shape(ghost):
    """display_data matches what the game words view consumes."""
    data = GhostReplay(ghost).display_data(450)

    assert data == {
        "target_words": ["hi", "there"],
        "typed_words": ["hi"],
        "current_word_index": 1,
        "current_input": "",
    }


def test_time_to_reach_chars(ghost):
    """Progress lookup returns the first moment a char count was reached."""
    replay = GhostReplay(ghost)

    assert replay.time_to_reach_chars(0) == 0
    assert replay.time_to_reach_chars(1) == 0  # "h" at t=0
    assert replay.time_to_reach_chars(2) == 100  # "hx" (typos count as progress)
    assert replay.time_to_reach_chars(3) == 500  # "hi" + "t"
    assert replay.time_to_reach_chars(7) == 900  # "hi" + "there"
    assert replay.time_to_reach_chars(8) is None  # never typed this far
