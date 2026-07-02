"""Tests for BaseGame input processing and statistics."""

import time

import pytest

from termtypr.games.base_game import BaseGame, GameStatus


class FakeGame(BaseGame):
    """Minimal concrete game with fixed target words."""

    def __init__(self, words: list[str]):
        super().__init__(name="Fake", description="test game")
        self._words = words

    def initialize(self, **kwargs) -> bool:
        """Mark the game ready."""
        self.status = GameStatus.READY
        return True

    def start(self) -> bool:
        """Set fixed target words and reset state."""
        self.target_words = list(self._words)
        self._reset_state()
        self.status = GameStatus.READY
        return True


@pytest.fixture
def game():
    """A started two-word game."""
    g = FakeGame(["hello", "world"])
    g.initialize()
    g.start()
    return g


def type_word(game: BaseGame, word: str) -> None:
    """Feed a word into the game one character at a time."""
    for i in range(1, len(word) + 1):
        game.process_input(word[:i], is_complete_input=False)


class TestKeystrokeTracking:
    """Tests for keystroke and error counting."""

    def test_correct_typing_counts_keystrokes_no_errors(self, game):
        """Every added character is a keystroke; correct ones aren't errors."""
        type_word(game, "hello")
        assert game.total_keystrokes == 5
        assert game.error_count == 0

    def test_single_typo_does_not_cascade(self, game):
        """A typo counts once; later correct-position chars aren't errors."""
        type_word(game, "hxllo")
        assert game.total_keystrokes == 5
        assert game.error_count == 1

    def test_backspace_not_counted(self, game):
        """Removing characters adds no keystrokes or errors."""
        type_word(game, "hex")
        game.process_input("he", is_complete_input=False)
        assert game.total_keystrokes == 3
        assert game.error_count == 1

    def test_wrong_word_submission_counts_submit_error(self, game):
        """Submitting a non-matching word counts the space as one error."""
        type_word(game, "he")
        game.process_input("he", is_complete_input=True)
        assert game.total_keystrokes == 3  # 'h', 'e' + submitting space
        assert game.error_count == 1

    def test_correct_word_submission_counts_correct_keystroke(self, game):
        """Submitting a matching word counts the space as a correct keystroke."""
        type_word(game, "hello")
        game.process_input("hello", is_complete_input=True)
        assert game.total_keystrokes == 6
        assert game.error_count == 0


class TestLastWordAutoComplete:
    """Tests for the test ending on the last correctly typed character."""

    def test_last_word_completes_without_space(self, game):
        """Typing the final word correctly finishes the game immediately."""
        game.process_input("hello", is_complete_input=True)
        type_word(game, "world")
        assert game.status == GameStatus.COMPLETED
        assert game.current_word_index == 2

    def test_auto_complete_adds_no_extra_keystroke(self, game):
        """No space is typed on auto-complete, so none is counted."""
        game.process_input("hello", is_complete_input=True)
        type_word(game, "world")
        # 1 submit space + 5 chars of 'world' (word one submitted directly)
        assert game.total_keystrokes == 6

    def test_non_last_word_does_not_auto_complete(self, game):
        """Typing a middle word correctly still waits for the space."""
        type_word(game, "hello")
        assert game.status == GameStatus.ACTIVE
        assert game.current_word_index == 0


class TestCurrentStats:
    """Tests for live statistics."""

    def test_in_progress_word_included(self, game):
        """Live stats count the word currently being typed."""
        game.process_input("hello", is_complete_input=True)
        type_word(game, "wor")
        stats = game.get_current_stats()
        assert stats["characters_typed"] == 8  # 'hello' + 'wor'

    def test_in_progress_word_untyped_tail_not_penalized(self, game):
        """A partially typed word's remaining characters aren't errors."""
        type_word(game, "h")  # correct first char of 'hello'
        game.start_time -= 60
        stats = game.get_current_stats()
        # 1 correct char in ~60s -> 0.2 WPM; counting the 4 untyped chars
        # of 'hello' as errors would clamp this to 0
        assert stats["wpm"] > 0

    def test_stats_before_start(self, game):
        """Before any input, stats are zeroed with 100% accuracy."""
        stats = game.get_current_stats()
        assert stats["wpm"] == 0.0
        assert stats["accuracy"] == 100.0
        assert stats["elapsed_time"] == 0.0


class TestFinish:
    """Tests for final results."""

    def test_finish_computes_wpm_and_raw_wpm(self, game):
        """Finished games report both net and raw WPM."""
        game.process_input("hello", is_complete_input=True)
        game.process_input("world", is_complete_input=True)
        game.start_time = time.time() - 60  # pretend the game took a minute

        result = game.finish()

        assert result.wpm == 2.2  # 11 chars incl. space, no errors
        assert result.raw_wpm == 2.2
        assert result.accuracy == 100.0

    def test_finish_penalizes_uncorrected_errors_in_wpm_only(self, game):
        """Wrong submissions lower net WPM but not raw WPM."""
        game.process_input("hxllo", is_complete_input=True)
        game.process_input("world", is_complete_input=True)
        game.start_time = time.time() - 60

        result = game.finish()

        assert result.wpm < result.raw_wpm
