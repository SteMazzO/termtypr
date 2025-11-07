"""Phrase typing game implementation."""

from src.core.phrase_generator import PhraseGenerator
from src.games.base_game import BaseGame, GameStatus


class PhraseTypingGame(BaseGame):
    """A typing game that presents phrases broken into words for the user to type."""

    def __init__(self, save_history: bool = True):
        super().__init__(
            name="Phrase Typing",
            description="Type complete phrases and quotes to improve your typing flow",
            save_history=save_history,
        )

        # Game configuration
        self.phrase_generator = PhraseGenerator()

    def initialize(self, **kwargs) -> bool:
        """Initialize the game with configuration."""
        self.status = GameStatus.READY
        return True

    def start(self) -> bool:
        """Start the phrase typing game."""
        if self.status != GameStatus.READY:
            return False

        try:
            # Generate target phrase and split into words
            self.target_words = self.phrase_generator.get_random_phrase().split()

            # Reset game state
            self.typed_words = []
            self.current_word_index = 0
            self.start_time = 0.0
            self.end_time = 0.0
            self.error_count = 0
            self.current_input = ""

            self.status = GameStatus.READY
            return True
        except Exception:  # noqa
            return False
