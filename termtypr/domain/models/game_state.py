"""Game state model and state machine."""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class GameStatus(Enum):
    """Status of a typing game."""

    NOT_STARTED = "not_started"
    READY = "ready"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

    def can_transition_to(self, new_status: "GameStatus") -> bool:
        """Check if transition to new status is valid."""
        valid_transitions = {
            GameStatus.NOT_STARTED: [GameStatus.READY],
            GameStatus.READY: [GameStatus.ACTIVE, GameStatus.CANCELLED],
            GameStatus.ACTIVE: [
                GameStatus.PAUSED,
                GameStatus.COMPLETED,
                GameStatus.CANCELLED,
            ],
            GameStatus.PAUSED: [GameStatus.ACTIVE, GameStatus.CANCELLED],
            GameStatus.COMPLETED: [],
            GameStatus.CANCELLED: [],
        }
        return new_status in valid_transitions.get(self, [])


@dataclass
class GameState:
    """Represents the current state of a typing game.

    This is a domain model that tracks all state information
    needed during a typing game session.
    """

    status: GameStatus
    target_words: list[str]
    typed_words: list[str]
    current_word_index: int
    current_input: str
    start_time: float
    end_time: float
    error_count: int

    @classmethod
    def create_initial(cls) -> "GameState":
        """Create initial game state."""
        return cls(
            status=GameStatus.NOT_STARTED,
            target_words=[],
            typed_words=[],
            current_word_index=0,
            current_input="",
            start_time=0.0,
            end_time=0.0,
            error_count=0,
        )

    @classmethod
    def create_ready(cls, target_words: list[str]) -> "GameState":
        """Create game state ready to start."""
        return cls(
            status=GameStatus.READY,
            target_words=target_words,
            typed_words=[],
            current_word_index=0,
            current_input="",
            start_time=0.0,
            end_time=0.0,
            error_count=0,
        )

    def transition_to(self, new_status: GameStatus) -> "GameState":
        """Create new state with updated status.

        Args:
            new_status: The new status to transition to

        Returns:
            New GameState instance with updated status

        Raises:
            ValueError: If transition is not valid
        """
        if not self.status.can_transition_to(new_status):
            raise ValueError(
                f"Cannot transition from {self.status.value} to {new_status.value}"
            )

        # Create new state with updated status
        return GameState(
            status=new_status,
            target_words=self.target_words,
            typed_words=self.typed_words,
            current_word_index=self.current_word_index,
            current_input=self.current_input,
            start_time=self.start_time,
            end_time=self.end_time,
            error_count=self.error_count,
        )

    def with_updates(
        self,
        typed_words: Optional[list[str]] = None,
        current_word_index: Optional[int] = None,
        current_input: Optional[str] = None,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None,
        error_count: Optional[int] = None,
    ) -> "GameState":
        """Create new state with updated fields.

        This follows the immutable pattern - returns a new instance.
        """
        return GameState(
            status=self.status,
            target_words=self.target_words,
            typed_words=typed_words if typed_words is not None else self.typed_words,
            current_word_index=(
                current_word_index
                if current_word_index is not None
                else self.current_word_index
            ),
            current_input=(
                current_input if current_input is not None else self.current_input
            ),
            start_time=start_time if start_time is not None else self.start_time,
            end_time=end_time if end_time is not None else self.end_time,
            error_count=error_count if error_count is not None else self.error_count,
        )

    @property
    def is_active(self) -> bool:
        """Check if game is currently active."""
        return self.status == GameStatus.ACTIVE

    @property
    def is_finished(self) -> bool:
        """Check if game is finished."""
        return self.status in [GameStatus.COMPLETED, GameStatus.CANCELLED]

    @property
    def current_target_word(self) -> Optional[str]:
        """Get the current target word."""
        if self.current_word_index < len(self.target_words):
            return self.target_words[self.current_word_index]
        return None

    @property
    def elapsed_time(self) -> float:
        """Calculate elapsed time."""
        if self.start_time == 0:
            return 0.0
        if self.end_time > 0:
            return self.end_time - self.start_time
        # Game is still active, use current time would require time.time()
        # For now, return 0 if not ended
        return 0.0

    @property
    def words_remaining(self) -> int:
        """Calculate number of words remaining."""
        return max(0, len(self.target_words) - self.current_word_index)

    @property
    def completion_percentage(self) -> float:
        """Calculate completion percentage."""
        if not self.target_words:
            return 0.0
        return (self.current_word_index / len(self.target_words)) * 100

    def to_dict(self) -> dict:
        """Convert to dictionary representation."""
        return {
            "status": self.status.value,
            "target_words": self.target_words,
            "typed_words": self.typed_words,
            "current_word_index": self.current_word_index,
            "current_input": self.current_input,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "error_count": self.error_count,
        }
