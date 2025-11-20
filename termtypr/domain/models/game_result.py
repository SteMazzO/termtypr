"""Domain model for game results."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class GameResult:
    """Represents the result of a completed typing game."""

    wpm: float
    accuracy: float
    duration: float
    game_type: str
    timestamp: datetime
    total_characters: int = 0
    correct_characters: int = 0
    error_count: int = 0
    is_new_record: bool = False
    previous_best: Optional[float] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "wpm": self.wpm,
            "accuracy": self.accuracy,
            "duration": self.duration,
            "game": self.game_type,
            "date": self.timestamp.isoformat(),
            "total_characters": self.total_characters,
            "correct_characters": self.correct_characters,
            "error_count": self.error_count,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "GameResult":
        """Create GameResult from dictionary."""
        return cls(
            wpm=data.get("wpm", 0.0),
            accuracy=data.get("accuracy", 0.0),
            duration=data.get("duration", 0.0),
            game_type=data.get("game", "Unknown"),
            timestamp=(
                datetime.fromisoformat(data["date"])
                if "date" in data
                else datetime.now()
            ),
            total_characters=data.get("total_characters", 0),
            correct_characters=data.get("correct_characters", 0),
            error_count=data.get("error_count", 0),
        )
