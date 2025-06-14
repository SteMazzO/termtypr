"""Base class for all typing games/tests."""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Optional


class GameStatus(Enum):
    """Status of a typing game."""

    NOT_STARTED = "not_started"
    READY = "ready"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class GameResult:
    """Result of a completed typing game."""

    def __init__(
        self,
        wpm: float,
        accuracy: float,
        duration: float,
        total_characters: int,
        correct_characters: int,
        error_count: int,
        is_new_record: bool = False,
        previous_best: Optional[float] = None,
        additional_data: Optional[dict[str, Any]] = None,
    ):
        self.wpm = wpm
        self.accuracy = accuracy
        self.duration = duration
        self.total_characters = total_characters
        self.correct_characters = correct_characters
        self.error_count = error_count
        self.is_new_record = is_new_record
        self.previous_best = previous_best
        self.additional_data = additional_data or {}

    def to_dict(self) -> dict[str, Any]:
        """Convert result to dictionary format."""
        return {
            "wpm": self.wpm,
            "accuracy": self.accuracy,
            "duration": self.duration,
            "total_characters": self.total_characters,
            "correct_characters": self.correct_characters,
            "error_count": self.error_count,
            "is_new_record": self.is_new_record,
            "previous_best": self.previous_best,
            **self.additional_data,
        }


class BaseGame(ABC):
    """Abstract base class for all typing games."""

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.status = GameStatus.NOT_STARTED
        self.result: Optional[GameResult] = None

    @abstractmethod
    def get_display_data(self) -> dict[str, Any]:
        """Get data needed for UI display.

        Returns:
            Dictionary containing display data like text to show,
            current progress, etc.
        """

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

    @abstractmethod
    def process_input(
        self, input_text: str, is_complete_input: bool = False
    ) -> dict[str, Any]:
        """Process user input.

        Args:
            input_text: The text input from the user
            is_complete_input: Whether this represents a complete input unit
                              (e.g., a complete word)

        Returns:
            Dictionary with processing result and any state changes
        """

    @abstractmethod
    def get_current_stats(self) -> dict[str, Any]:
        """Get current game statistics.

        Returns:
            Dictionary with current statistics (WPM, accuracy, etc.)
        """

    @abstractmethod
    def finish(self) -> GameResult:
        """Finish the game and return results.

        Returns:
            GameResult object with final statistics
        """

    @abstractmethod
    def reset(self) -> None:
        """Reset the game to initial state."""

    def pause(self) -> bool:
        """Pause the game if possible.

        Returns:
            True if game was paused, False if pausing is not supported
        """
        if self.status == GameStatus.ACTIVE:
            self.status = GameStatus.PAUSED
            return True
        return False

    def resume(self) -> bool:
        """Resume a paused game.

        Returns:
            True if game was resumed, False if not paused or resume failed
        """
        if self.status == GameStatus.PAUSED:
            self.status = GameStatus.ACTIVE
            return True
        return False

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
