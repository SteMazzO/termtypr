"""Phrase typing game implementation."""

from termtypr.core.phrase_generator import get_random_phrase
from termtypr.games.base_game import BaseGame, GameStatus


class PhraseTypingGame(BaseGame):
    """Typing game where players type complete phrases and quotes."""

    DISPLAY_NAME = "Phrase Typing"
    GAME_DESCRIPTION = "Type complete phrases and quotes to improve your typing flow"

    def __init__(self):
        super().__init__(
            name=self.DISPLAY_NAME,
            description=self.GAME_DESCRIPTION,
        )

    def initialize(self, **kwargs) -> bool:
        """Initialize the game with configuration."""
        self.status = GameStatus.READY
        return True

    def start(self) -> bool:
        """Start the phrase typing game."""
        if self.status != GameStatus.READY:
            return False

        self.target_words = get_random_phrase().split()
        self._reset_state()
        self.status = GameStatus.READY
        return True
