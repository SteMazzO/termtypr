"""Base class for all typing games/tests."""

import time
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Optional

from src.core.stats_calculator import StatsCalculator
from src.domain.models.game_result import GameResult
from src.domain.models.game_state import GameStatus


class BaseGame(ABC):
    """Abstract base class for all typing games."""

    def __init__(self, name: str, description: str, save_history: bool = True):
        """Initialize the base game.

        Args:
            name: Name of the game
            description: Description of the game
            save_history: Whether to save to history (deprecated, kept for compatibility)
        """
        self.name = name
        self.description = description
        self.status = GameStatus.NOT_STARTED
        self.result: Optional[GameResult] = None
        self.save_history = save_history  # Kept for backward compatibility

        # Game state
        self.target_words: list[str] = []
        self.typed_words: list[str] = []
        self.current_word_index = 0
        self.start_time = 0.0
        self.end_time = 0.0
        self.error_count = 0
        self.current_input = ""
        self.previous_input = ""  # Track previous state to detect new errors

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

    def is_active(self) -> bool:
        """Check if the game is currently active."""
        return self.status == GameStatus.ACTIVE

    def is_finished(self) -> bool:
        """Check if the game is finished (completed or cancelled)."""
        return self.status in [GameStatus.COMPLETED, GameStatus.CANCELLED]

    def get_configuration_schema(self) -> dict[str, Any]:
        """Get the configuration schema for this game type.

        Returns:
            Dictionary describing the configuration options for this game
        """
        return {}

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

    def _process_complete_word(self, word: str) -> dict[str, Any]:
        """Process a complete word input. Always count every submitted word, correct or not."""
        if self.current_word_index >= len(self.target_words):
            # Already finished
            self.status = GameStatus.COMPLETED
            return {"status": "complete", "message": "All words completed"}

        # Ensure typed_words has a slot for every attempted word
        while len(self.typed_words) <= self.current_word_index:
            self.typed_words.append("")

        # Store the typed word
        self.typed_words[self.current_word_index] = word

        # Don't count errors here - they're already tracked in _process_partial_input
        # during character-by-character typing

        # Move to next word
        self.current_word_index += 1
        self.current_input = ""
        self.previous_input = ""  # Reset for next word

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
        # Track errors only when new characters are added (not on backspace)
        if self.current_word_index < len(self.target_words):
            target_word = self.target_words[self.current_word_index]

            if len(input_text) > len(self.previous_input):
                if input_text and not target_word.startswith(input_text):
                    self.error_count += 1

        self.previous_input = input_text
        self.current_input = input_text

        # Ensure we have space in typed_words for current progress
        while len(self.typed_words) <= self.current_word_index:
            self.typed_words.append("")

        # Update current word in typed_words (for real-time display)
        self.typed_words[self.current_word_index] = input_text

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
                "accuracy": 100.0,
                "elapsed_time": 0.0,
                "characters_typed": 0,
            }

        elapsed_time = time.time() - self.start_time

        # Use only completed words for stats calculation
        completed_typed_words = self.typed_words[: self.current_word_index]
        completed_target_words = self.target_words[: self.current_word_index]

        if completed_typed_words:
            stats = StatsCalculator.get_statistics(
                completed_typed_words,
                completed_target_words,
                elapsed_time,
                self.error_count,
            )
        else:
            stats = {"wpm": 0.0, "accuracy": 100.0, "duration": elapsed_time}

        stats.update(
            {
                "elapsed_time": elapsed_time,
                "total_words": len(self.target_words),
                "characters_typed": sum(len(word) for word in completed_typed_words),
            }
        )

        return stats

    def finish(self) -> GameResult:
        """Finish the game and return results."""
        if self.status != GameStatus.COMPLETED:
            # Force finish if not already completed
            self.status = GameStatus.COMPLETED

        self.end_time = time.time()
        elapsed_time = self.end_time - self.start_time if self.start_time > 0 else 0.0

        # Calculate final statistics
        stats = StatsCalculator.get_statistics(
            self.typed_words[: self.current_word_index],
            self.target_words[: self.current_word_index],
            elapsed_time,
            self.error_count,
        )

        # Check for new record - note: this is now handled by GameController
        # Kept here for backward compatibility with direct game usage
        is_new_record = False
        previous_best = None

        # Create result object
        completed_typed = self.typed_words[: self.current_word_index]
        completed_target = self.target_words[: self.current_word_index]

        self.result = GameResult(
            wpm=stats["wpm"],
            accuracy=stats["accuracy"],
            duration=elapsed_time,
            game_type=self.name,
            timestamp=datetime.now(),
            total_characters=sum(len(word) for word in completed_target),
            correct_characters=sum(
                len(typed)
                for typed, target in zip(completed_typed, completed_target)
                if typed == target
            ),
            error_count=self.error_count,
            is_new_record=is_new_record,
            previous_best=previous_best,
        )

        return self.result

    def reset(self) -> None:
        """Reset the game to initial state."""
        self.target_words = []
        self.typed_words = []
        self.current_word_index = 0
        self.start_time = 0.0
        self.end_time = 0.0
        self.error_count = 0
        self.current_input = ""
        self.previous_input = ""
        self.status = GameStatus.NOT_STARTED
        self.result = None

    def get_elapsed_time(self) -> float:
        """Get elapsed time since game started."""
        if not self.start_time:
            return 0.0

        if self.end_time > 0.0:
            return self.end_time - self.start_time

        return time.time() - self.start_time
