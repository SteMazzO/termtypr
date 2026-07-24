"""Tests for PhraseTypingGame."""

from termtypr.games.base_game import GameStatus
from termtypr.games.phrase_typing_game import PhraseTypingGame


def make_started_game() -> PhraseTypingGame:
    """Create an initialized and started phrase game."""
    game = PhraseTypingGame()
    assert game.initialize()
    assert game.start()
    return game


def test_start_retains_original_phrase():
    """start() keeps the full phrase string, consistent with target_words."""
    game = make_started_game()

    assert game.phrase_text is not None
    assert game.phrase_text.split() == game.target_words


def test_start_requires_ready_status():
    """start() fails unless the game was initialized first."""
    game = PhraseTypingGame()
    assert game.start() is False


def test_finish_result_carries_phrase_identity():
    """The GameResult of a phrase run includes the phrase text and hash."""
    game = make_started_game()

    for word in game.target_words:
        game.process_input(word, is_complete_input=True)
    game.start_time -= 60  # ensure a meaningful elapsed time

    result = game.finish()

    assert game.status == GameStatus.COMPLETED
    assert result.phrase_text == game.phrase_text
    assert result.phrase_hash is not None
