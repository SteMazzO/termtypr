"""Tests for GameController."""

import pytest

from src.application.controllers.game_controller import GameController
from src.domain.models.game_state import GameStatus
from src.games.random_words_game import RandomWordsGame
from src.infrastructure.persistence.memory_history_repository import (
    InMemoryHistoryRepository,
)


@pytest.fixture
def history_repo():
    """Create an in-memory history repository for testing."""
    return InMemoryHistoryRepository()


@pytest.fixture
def controller(history_repo):
    """Create a game controller for testing."""
    return GameController(history_repo)


@pytest.fixture
def game_instance():
    """Create a game instance for testing."""
    return RandomWordsGame(save_history=False)


def test_controller_initialization(controller):
    """Test that controller initializes correctly."""
    assert controller.current_game is None
    assert controller.game_state is None
    assert not controller.is_game_active()


def test_start_game_success(controller, game_instance):
    """Test starting a game successfully."""
    result = controller.start_game(game_instance, {"word_count": 10})

    assert result is True
    assert controller.current_game is not None
    assert controller.game_state is not None
    assert controller.game_state.status == GameStatus.READY
    assert len(controller.game_state.target_words) == 10


def test_start_game_with_defaults(controller, game_instance):
    """Test starting a game with default configuration."""
    result = controller.start_game(game_instance)

    assert result is True
    assert controller.current_game is not None
    # Should use default from settings (20 words)
    assert len(controller.game_state.target_words) == 20


def test_start_game_invalid_config(controller, game_instance):
    """Test starting a game with invalid configuration."""
    # Invalid word count (too high)
    result = controller.start_game(game_instance, {"word_count": 200})

    assert result is False
    assert controller.current_game is None


def test_process_input_no_game(controller):
    """Test processing input when no game is active."""
    result = controller.process_input("test", False)

    assert result["status"] == "error"
    assert "No active game" in result["message"]


def test_process_input_activates_game(controller, game_instance):
    """Test that processing input activates the game."""
    controller.start_game(game_instance, {"word_count": 5})

    assert controller.game_state.status == GameStatus.READY

    # Process first input
    controller.process_input("t", False)

    # Game should now be active
    assert controller.game_state.status == GameStatus.ACTIVE


def test_process_complete_word(controller, game_instance):
    """Test processing a complete word."""
    controller.start_game(game_instance, {"word_count": 5})

    # Get the first target word
    first_word = controller.game_state.target_words[0]

    # Submit the complete word
    result = controller.process_input(first_word, is_complete=True)

    assert result["status"] in ["active", "complete"]
    assert controller.game_state.current_word_index == 1


def test_game_completion(controller):
    """Test completing all words in the game."""
    game_instance = RandomWordsGame(save_history=False)
    started = controller.start_game(game_instance, {"word_count": 5})

    assert started, "Game should start successfully"
    assert controller.current_game is not None, "Current game should be set"

    # Complete all words
    for word in controller.current_game.target_words:
        controller.process_input(word, is_complete=True)

    # Game should be completed
    assert controller.current_game.status == GameStatus.COMPLETED


def test_get_current_stats_no_game(controller):
    """Test getting stats when no game is active."""
    stats = controller.get_current_stats()

    assert abs(stats["wpm"] - 0.0) < 0.01
    assert abs(stats["accuracy"] - 100.0) < 0.01
    assert abs(stats["elapsed_time"] - 0.0) < 0.01


def test_get_current_stats_active_game(controller, game_instance):
    """Test getting stats during an active game."""
    controller.start_game(game_instance, {"word_count": 5})

    # Process some input
    first_word = controller.game_state.target_words[0]
    controller.process_input(first_word, is_complete=True)

    stats = controller.get_current_stats()

    assert "wpm" in stats
    assert "accuracy" in stats
    assert "elapsed_time" in stats


def test_get_display_data_no_game(controller):
    """Test getting display data when no game exists."""
    data = controller.get_display_data()

    assert data == {}


def test_get_display_data_active_game(controller, game_instance):
    """Test getting display data during a game."""
    controller.start_game(game_instance, {"word_count": 5})

    data = controller.get_display_data()

    assert "target_words" in data
    assert "typed_words" in data
    assert "current_word_index" in data
    assert "status" in data
    assert "words_remaining" in data
    assert "completion_percentage" in data
    assert data["status"] == GameStatus.READY.value


def test_finish_game_saves_to_history(controller, history_repo):
    """Test that finishing a game saves the result to history."""
    game_instance = RandomWordsGame(save_history=False)
    controller.start_game(game_instance, {"word_count": 5})

    # Complete the game
    for word in controller.current_game.target_words:
        controller.process_input(word, is_complete=True)

    # Finish and get result
    result = controller.finish_game()

    assert result is not None
    assert result.wpm >= 0
    assert result.accuracy >= 0

    # Verify it was saved to history
    history = history_repo.get_all()
    assert len(history) == 1
    assert history[0].wpm == result.wpm


def test_finish_game_no_active_game(controller):
    """Test finishing when no game is active."""
    with pytest.raises(RuntimeError, match="No active game"):
        controller.finish_game()


def test_finish_game_new_record(controller, history_repo):
    """Test that new records are detected correctly."""
    # Start and finish first game
    game1 = RandomWordsGame(save_history=False)
    controller.start_game(game1, {"word_count": 5})
    for word in controller.current_game.target_words:
        controller.process_input(word, is_complete=True)

    result1 = controller.finish_game()

    # Reset and start second game
    controller.reset()
    game2 = RandomWordsGame(save_history=False)
    controller.start_game(game2, {"word_count": 5})
    for word in controller.current_game.target_words:
        controller.process_input(word, is_complete=True)

    controller.finish_game()

    # First result should be marked as new record
    assert result1.is_new_record is True
    # Second might or might not be depending on WPM


def test_cancel_game(controller, game_instance):
    """Test canceling a game."""
    controller.start_game(game_instance, {"word_count": 5})

    # Process some input
    controller.process_input("test", False)

    # Cancel the game
    controller.cancel_game()

    assert controller.current_game is None
    assert controller.game_state is None
    assert not controller.is_game_active()


def test_reset_controller(controller, game_instance):
    """Test resetting the controller."""
    controller.start_game(game_instance, {"word_count": 5})
    controller.process_input("test", False)

    controller.reset()

    assert controller.current_game is None
    assert controller.game_state is None


def test_is_game_active(controller, game_instance):
    """Test checking if game is active."""
    assert not controller.is_game_active()

    controller.start_game(game_instance, {"word_count": 5})
    assert not controller.is_game_active()  # Not active until first input

    controller.process_input("t", False)
    assert controller.is_game_active()  # Now active


def test_is_game_finished(controller):
    """Test checking if game is finished."""
    assert not controller.is_game_finished()

    game_instance = RandomWordsGame(save_history=False)
    controller.start_game(game_instance, {"word_count": 5})

    # Complete all words
    for word in controller.current_game.target_words:
        controller.process_input(word, is_complete=True)

    controller.finish_game()
    assert controller.is_game_finished()


def test_get_game_state(controller, game_instance):
    """Test getting the game state."""
    assert controller.get_game_state() is None

    controller.start_game(game_instance, {"word_count": 5})

    state = controller.get_game_state()
    assert state is not None
    assert state.status == GameStatus.READY
    assert len(state.target_words) == 5


def test_get_elapsed_time_no_game(controller):
    """Test getting elapsed time when no game exists."""
    assert abs(controller.get_elapsed_time() - 0.0) < 0.01


def test_get_elapsed_time_active_game(controller, game_instance):
    """Test getting elapsed time during a game."""
    controller.start_game(game_instance, {"word_count": 5})

    # Start by typing something
    controller.process_input("test", False)

    elapsed = controller.get_elapsed_time()
    assert elapsed >= 0.0
