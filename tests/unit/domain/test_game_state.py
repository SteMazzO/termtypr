"""Tests for GameState model."""

import pytest

from src.domain.models.game_state import GameState, GameStatus


def test_create_initial_state():
    """Test creating initial game state."""
    state = GameState.create_initial()

    assert state.status == GameStatus.NOT_STARTED
    assert state.target_words == []
    assert state.typed_words == []
    assert state.current_word_index == 0
    assert state.error_count == 0


def test_create_ready_state():
    """Test creating ready game state."""
    words = ["hello", "world", "test"]
    state = GameState.create_ready(words)

    assert state.status == GameStatus.READY
    assert state.target_words == words
    assert state.typed_words == []


def test_valid_status_transition():
    """Test valid status transition."""
    state = GameState.create_initial()

    # NOT_STARTED -> READY is valid
    new_state = state.transition_to(GameStatus.READY)
    assert new_state.status == GameStatus.READY


def test_invalid_status_transition():
    """Test invalid status transition raises error."""
    state = GameState.create_initial()

    # NOT_STARTED -> COMPLETED is invalid
    with pytest.raises(ValueError, match="Cannot transition"):
        state.transition_to(GameStatus.COMPLETED)


def test_transition_preserves_data():
    """Test that transition preserves game data."""
    words = ["hello", "world"]
    state = GameState.create_ready(words)
    state = state.with_updates(typed_words=["hello"], current_word_index=1)

    # Transition to ACTIVE
    new_state = state.transition_to(GameStatus.ACTIVE)

    assert new_state.target_words == words
    assert new_state.typed_words == ["hello"]
    assert new_state.current_word_index == 1


def test_with_updates():
    """Test updating state fields."""
    state = GameState.create_ready(["hello", "world"])

    new_state = state.with_updates(
        typed_words=["hello"], current_word_index=1, error_count=2
    )

    assert new_state.typed_words == ["hello"]
    assert new_state.current_word_index == 1
    assert new_state.error_count == 2
    # Original unchanged
    assert state.typed_words == []
    assert state.error_count == 0


def test_is_active():
    """Test is_active property."""
    state = GameState.create_ready(["hello"])
    assert not state.is_active

    active_state = state.transition_to(GameStatus.ACTIVE)
    assert active_state.is_active


def test_is_finished():
    """Test is_finished property."""
    state = GameState.create_ready(["hello"])
    state = state.transition_to(GameStatus.ACTIVE)
    assert not state.is_finished

    completed_state = state.transition_to(GameStatus.COMPLETED)
    assert completed_state.is_finished

    cancelled_state = state.transition_to(GameStatus.CANCELLED)
    assert cancelled_state.is_finished


def test_current_target_word():
    """Test current_target_word property."""
    state = GameState.create_ready(["hello", "world", "test"])

    assert state.current_target_word == "hello"

    new_state = state.with_updates(current_word_index=1)
    assert new_state.current_target_word == "world"

    # Beyond end
    end_state = state.with_updates(current_word_index=10)
    assert end_state.current_target_word is None


def test_words_remaining():
    """Test words_remaining property."""
    state = GameState.create_ready(["hello", "world", "test"])

    assert state.words_remaining == 3

    new_state = state.with_updates(current_word_index=1)
    assert new_state.words_remaining == 2

    end_state = state.with_updates(current_word_index=3)
    assert end_state.words_remaining == 0


def test_completion_percentage():
    """Test completion_percentage property."""
    state = GameState.create_ready(["hello", "world", "test", "game"])

    assert state.completion_percentage == 0.0

    half_state = state.with_updates(current_word_index=2)
    assert half_state.completion_percentage == 50.0

    complete_state = state.with_updates(current_word_index=4)
    assert complete_state.completion_percentage == 100.0


def test_to_dict():
    """Test conversion to dictionary."""
    state = GameState.create_ready(["hello", "world"])
    state = state.with_updates(typed_words=["hello"], current_word_index=1)

    data = state.to_dict()

    assert data["status"] == "ready"
    assert data["target_words"] == ["hello", "world"]
    assert data["typed_words"] == ["hello"]
    assert data["current_word_index"] == 1


def test_state_transitions_chain():
    """Test chaining multiple state transitions."""
    state = GameState.create_initial()

    # Full game lifecycle
    state = state.transition_to(GameStatus.READY)
    assert state.status == GameStatus.READY

    state = state.transition_to(GameStatus.ACTIVE)
    assert state.status == GameStatus.ACTIVE

    state = state.transition_to(GameStatus.PAUSED)
    assert state.status == GameStatus.PAUSED

    state = state.transition_to(GameStatus.ACTIVE)
    assert state.status == GameStatus.ACTIVE

    state = state.transition_to(GameStatus.COMPLETED)
    assert state.status == GameStatus.COMPLETED
