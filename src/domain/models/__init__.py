"""Domain models for TermTypr."""

from src.domain.models.game_result import GameResult
from src.domain.models.game_state import GameState, GameStatus
from src.domain.models.typing_stats import TypingStats

__all__ = ["GameResult", "GameState", "GameStatus", "TypingStats"]
