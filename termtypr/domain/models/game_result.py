"""Domain model for game results."""

from dataclasses import dataclass
from datetime import datetime

from termtypr.core.phrase_hash import phrase_hash


@dataclass(frozen=True)
class GameResult:
    """Represents the result of a completed typing game."""

    wpm: float
    accuracy: float
    duration: float
    game_type: str
    timestamp: datetime
    raw_wpm: float = 0.0
    total_characters: int = 0
    correct_characters: int = 0
    error_count: int = 0
    phrase_text: str | None = None
    is_new_record: bool = False
    previous_best: float | None = None

    @property
    def phrase_hash(self) -> str | None:
        """Stable identifier of the phrase this result was typed on."""
        if self.phrase_text is None:
            return None
        return phrase_hash(self.phrase_text)
