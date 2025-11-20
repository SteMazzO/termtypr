"""Value object for typing test statistics."""

from dataclasses import dataclass


@dataclass(frozen=True)
class TypingStats:
    """Immutable value object representing typing test statistics.

    This encapsulates all statistical data about a typing session,
    ensuring data integrity through immutability.
    """

    wpm: float
    accuracy: float
    duration: float
    typed_word_count: int
    target_word_count: int
    total_characters: int
    correct_characters: int
    error_count: int
    is_completed: bool

    def __post_init__(self):
        """Validate statistics values."""
        if self.wpm < 0:
            raise ValueError("WPM cannot be negative")
        if not 0 <= self.accuracy <= 100:
            raise ValueError("Accuracy must be between 0 and 100")
        if self.duration < 0:
            raise ValueError("Duration cannot be negative")
        if self.typed_word_count < 0:
            raise ValueError("Typed word count cannot be negative")
        if self.target_word_count < 0:
            raise ValueError("Target word count cannot be negative")
        if self.error_count < 0:
            raise ValueError("Error count cannot be negative")

    @property
    def completion_percentage(self) -> float:
        """Calculate completion percentage."""
        if self.target_word_count == 0:
            return 0.0
        return (self.typed_word_count / self.target_word_count) * 100

    @property
    def errors_per_word(self) -> float:
        """Calculate average errors per word typed."""
        if self.typed_word_count == 0:
            return 0.0
        return self.error_count / self.typed_word_count

    @property
    def characters_per_minute(self) -> float:
        """Calculate characters per minute."""
        if self.duration == 0:
            return 0.0
        return (self.total_characters / self.duration) * 60

    def to_dict(self) -> dict:
        """Convert to dictionary representation."""
        return {
            "wpm": self.wpm,
            "accuracy": self.accuracy,
            "duration": self.duration,
            "typed_word_count": self.typed_word_count,
            "target_word_count": self.target_word_count,
            "total_characters": self.total_characters,
            "correct_characters": self.correct_characters,
            "error_count": self.error_count,
            "is_completed": self.is_completed,
            "completion_percentage": self.completion_percentage,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "TypingStats":
        """Create TypingStats from dictionary."""
        return cls(
            wpm=data.get("wpm", 0.0),
            accuracy=data.get("accuracy", 0.0),
            duration=data.get("duration", 0.0),
            typed_word_count=data.get("typed_word_count", 0),
            target_word_count=data.get("target_word_count", 0),
            total_characters=data.get("total_characters", 0),
            correct_characters=data.get("correct_characters", 0),
            error_count=data.get("error_count", 0),
            is_completed=data.get("is_completed", False),
        )
