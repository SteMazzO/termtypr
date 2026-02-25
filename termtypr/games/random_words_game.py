"""Random words typing game implementation."""

from termtypr.core.word_generator import get_random_words
from termtypr.domain.models.user_preferences import (
    DEFAULT_WORD_COUNT,
    MAX_WORD_COUNT,
    MIN_WORD_COUNT,
)
from termtypr.games.base_game import BaseGame, GameStatus


class RandomWordsGame(BaseGame):
    """Typing game where players type randomly selected words."""

    DISPLAY_NAME = "Random Words"
    GAME_DESCRIPTION = "Type randomly selected words as fast and accurately as possible"

    def __init__(self):
        super().__init__(
            name=self.DISPLAY_NAME,
            description=self.GAME_DESCRIPTION,
        )

        # Game configuration
        self.word_count = DEFAULT_WORD_COUNT

    def initialize(self, **kwargs) -> bool:
        """Initialize the game with configuration."""
        self.word_count = kwargs.get("word_count", DEFAULT_WORD_COUNT)

        # Validate word count
        if not MIN_WORD_COUNT <= self.word_count <= MAX_WORD_COUNT:
            return False

        self.status = GameStatus.READY
        return True

    def start(self) -> bool:
        """Start the random words game."""
        if self.status != GameStatus.READY:
            return False

        self.target_words = get_random_words(self.word_count)
        self._reset_state()
        self.status = GameStatus.READY
        return True
