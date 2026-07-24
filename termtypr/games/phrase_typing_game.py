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

        self._reset_state()
        self.set_phrase(get_random_phrase())
        self.status = GameStatus.READY
        return True

    def set_phrase(self, phrase: str) -> None:
        """Replace the target phrase (used by rematches and ghost races).

        Any state derived from the phrase must be set here, so content
        injected from outside can never diverge from the drawn phrase.
        """
        self.target_words = phrase.split()
        self.phrase_text = phrase
