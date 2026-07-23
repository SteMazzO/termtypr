"""Base class for all typing games/tests."""

import time
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from termtypr.core.stats_calculator import (
    calculate_accuracy,
    calculate_raw_wpm,
    calculate_wpm,
)
from termtypr.domain.models.game_result import GameResult


class GameStatus(Enum):
    """Status of a typing game."""

    NOT_STARTED = "not_started"
    READY = "ready"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class BaseGame(ABC):
    """Abstract base class for all typing games."""

    def __init__(self, name: str, description: str):
        """Initialize the base game.

        Args:
            name: Name of the game
            description: Description of the game
        """
        self.name = name
        self.description = description
        self.status = GameStatus.NOT_STARTED
        self.result: GameResult | None = None

        # Game state
        self.target_words: list[str] = []
        # Original phrase string for phrase-based games (None otherwise);
        # target_words alone can't reproduce it exactly.
        self.phrase_text: str | None = None
        self.typed_words: list[str] = []
        self.current_word_index = 0
        self.start_time = 0.0
        self.end_time = 0.0
        self.error_count = 0
        self.total_keystrokes = 0
        self.current_input = ""
        self.previous_input = ""

    @abstractmethod
    def initialize(self, **kwargs) -> bool:
        """Initialize the game with given parameters.

        Args:
            **kwargs: Game-specific configuration parameters

        Returns:
            True if initialization was successful, False otherwise
        """

    @abstractmethod
    def start(self) -> bool:
        """Start the game.

        Returns:
            True if game started successfully, False otherwise
        """

    def cancel(self) -> None:
        """Cancel the current game."""
        self.status = GameStatus.CANCELLED
        self.result = None

    def elapsed_seconds(self) -> float | None:
        """Seconds since the run's first keystroke, or None before it.

        The single run clock: recording timestamps and replay playback
        must both derive from this so they can never drift apart.
        """
        if not self.start_time:
            return None
        return time.time() - self.start_time

    def progress_chars(self) -> int:
        """Characters of the target covered so far, capped per word.

        Unlike raw typed-character counts, over-typing a word cannot
        inflate this past the target's length, so it is a comparable
        progress metric between a player and a ghost.
        """
        covered = 0
        for i, typed in enumerate(self.typed_words[: self.current_word_index]):
            if i < len(self.target_words):
                covered += min(len(typed), len(self.target_words[i]))
        if self.current_word_index < len(self.target_words):
            target = self.target_words[self.current_word_index]
            covered += min(len(self.current_input), len(target))
        return covered

    def is_finished(self) -> bool:
        """Check if the game is finished (completed or cancelled)."""
        return self.status in [GameStatus.COMPLETED, GameStatus.CANCELLED]

    def get_display_data(self) -> dict[str, Any]:
        """Get data for UI display."""
        return {
            "target_words": self.target_words,
            "typed_words": self.typed_words,
            "current_word_index": self.current_word_index,
            "current_input": self.current_input,
            "total_words": len(self.target_words),
            "current_target_word": (
                self.target_words[self.current_word_index]
                if self.current_word_index < len(self.target_words)
                else ""
            ),
        }

    def process_input(
        self, input_text: str, is_complete_input: bool = False
    ) -> dict[str, Any]:
        """Process typing input."""
        # Start timer on first input
        if not self.start_time and input_text:
            self.status = GameStatus.ACTIVE
            self.start_time = time.time()

        if self.status != GameStatus.ACTIVE:
            return {"status": "inactive", "message": "Game is not active"}

        if is_complete_input:
            # Process a complete word
            return self._process_complete_word(input_text)
        # Process character-by-character input
        return self._process_partial_input(input_text)

    def _process_complete_word(
        self, word: str, is_keystroke: bool = True
    ) -> dict[str, Any]:
        """Process a complete word input.

        Always count every submitted word, correct or not.

        Args:
            word: The submitted word.
            is_keystroke: True when the submission came from an actual key
                press (space/enter), which then counts toward accuracy.
        """
        if self.current_word_index >= len(self.target_words):
            # Already finished
            self.status = GameStatus.COMPLETED
            return {"status": "complete", "message": "All words completed"}

        if is_keystroke:
            # The submitting space/enter is itself a keystroke: correct when
            # the word matches its target, an error otherwise.
            self.total_keystrokes += 1
            if word != self.target_words[self.current_word_index]:
                self.error_count += 1

        # Ensure typed_words has a slot for every attempted word
        while len(self.typed_words) <= self.current_word_index:
            self.typed_words.append("")

        self.typed_words[self.current_word_index] = word

        # Move to next word
        self.current_word_index += 1
        self.current_input = ""
        self.previous_input = ""

        # If all words have been attempted, mark as complete
        if self.current_word_index >= len(self.target_words):
            self.status = GameStatus.COMPLETED
            # Ensure typed_words length matches total words
            while len(self.typed_words) < len(self.target_words):
                self.typed_words.append("")
            return {"status": "complete", "message": "All words completed"}

        return {
            "status": "active",
            "word_completed": True,
            "current_index": self.current_word_index,
            "total_words": len(self.target_words),
        }

    def _process_partial_input(self, input_text: str) -> dict[str, Any]:
        """Process partial input (character by character)."""
        # Track keystrokes only when new characters are added (not on
        # backspace). Each added character is judged against its own target
        # position, so one typo doesn't cascade into errors for every
        # keystroke that follows it.
        if self.current_word_index < len(self.target_words):
            target_word = self.target_words[self.current_word_index]
            added = len(input_text) - len(self.previous_input)

            if input_text and added > 0:
                self.total_keystrokes += added
                self.error_count += sum(
                    1
                    for i in range(len(self.previous_input), len(input_text))
                    if i >= len(target_word) or input_text[i] != target_word[i]
                )

        self.previous_input = input_text
        self.current_input = input_text

        # Ensure we have space in typed_words for current progress
        while len(self.typed_words) <= self.current_word_index:
            self.typed_words.append("")

        # Update current word in typed_words
        self.typed_words[self.current_word_index] = input_text

        # The test ends the moment the last word is typed correctly; no
        # trailing space is needed.
        if (
            self.target_words
            and self.current_word_index == len(self.target_words) - 1
            and input_text == self.target_words[self.current_word_index]
        ):
            return self._process_complete_word(input_text, is_keystroke=False)

        return {
            "status": "active",
            "current_input": input_text,
            "current_index": self.current_word_index,
        }

    def get_current_stats(self) -> dict[str, Any]:
        """Get current game statistics."""
        if not self.start_time:
            return {
                "wpm": 0.0,
                "raw_wpm": 0.0,
                "accuracy": 100.0,
                "duration": 0.0,
                "elapsed_time": 0.0,
                "total_words": len(self.target_words),
                "characters_typed": 0,
            }

        elapsed_time = time.time() - self.start_time

        # Include the word currently being typed so live WPM doesn't sag
        # between word submissions.
        typed = self.typed_words[: self.current_word_index]
        targets = self.target_words[: self.current_word_index]
        if self.current_input and self.current_word_index < len(self.target_words):
            current_target = self.target_words[self.current_word_index]
            typed = [*typed, self.current_input]
            targets = [*targets, current_target[: len(self.current_input)]]

        return {
            "wpm": calculate_wpm(typed, targets, elapsed_time),
            "raw_wpm": calculate_raw_wpm(typed, elapsed_time),
            "accuracy": calculate_accuracy(self.total_keystrokes, self.error_count),
            "duration": round(elapsed_time, 2),
            "elapsed_time": elapsed_time,
            "total_words": len(self.target_words),
            "characters_typed": sum(len(word) for word in typed),
        }

    def finish(self) -> GameResult:
        """Finish the game and return results."""
        if self.status != GameStatus.COMPLETED:
            self.status = GameStatus.COMPLETED

        self.end_time = time.time()
        elapsed_time = self.end_time - self.start_time if self.start_time > 0 else 0.0

        completed_typed = self.typed_words[: self.current_word_index]
        completed_target = self.target_words[: self.current_word_index]

        wpm = calculate_wpm(completed_typed, completed_target, elapsed_time)
        raw_wpm = calculate_raw_wpm(completed_typed, elapsed_time)
        accuracy = calculate_accuracy(self.total_keystrokes, self.error_count)

        self.result = GameResult(
            wpm=wpm,
            raw_wpm=raw_wpm,
            accuracy=accuracy,
            duration=elapsed_time,
            game_type=self.name,
            timestamp=datetime.now(tz=timezone.utc),
            total_characters=sum(len(w) for w in completed_target),
            correct_characters=sum(
                len(typed)
                for typed, target in zip(
                    completed_typed, completed_target, strict=False
                )
                if typed == target
            ),
            error_count=self.error_count,
            phrase_text=self.phrase_text,
        )

        return self.result

    def _reset_state(self) -> None:
        """Reset mutable game state (called by subclass start())."""
        self.typed_words = []
        self.current_word_index = 0
        self.start_time = 0.0
        self.end_time = 0.0
        self.error_count = 0
        self.total_keystrokes = 0
        self.current_input = ""
        self.previous_input = ""
        self.result = None
