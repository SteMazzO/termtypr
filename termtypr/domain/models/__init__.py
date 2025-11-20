"""Domain models for TermTypr."""

from termtypr.domain.models.game_result import GameResult
from termtypr.domain.models.game_state import GameState, GameStatus
from termtypr.domain.models.typing_stats import TypingStats

__all__ = ["GameResult", "GameState", "GameStatus", "TypingStats"]
