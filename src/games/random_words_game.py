"""Random words typing game implementation."""

from src.core.word_generator import WordGenerator
from src.games.base_game import BaseGame, GameStatus


class RandomWordsGame(BaseGame):
    """A typing game that presents random words for the user to type."""

    def __init__(self, save_history: bool = True):
        super().__init__(
            name="Random Words",
            description="Type randomly selected words as fast and accurately as possible",
            save_history=save_history,
        )

        # Game configuration
        self.word_count = 20
        self.word_generator = WordGenerator()

    def initialize(self, **kwargs) -> bool:
        """Initialize the game with configuration."""
        self.word_count = kwargs.get("word_count", 20)

        # Validate word count
        if self.word_count < 5 or self.word_count > 100:
            return False

        self.status = GameStatus.READY
        return True

    def start(self) -> bool:
        """Start the random words game."""
        if self.status != GameStatus.READY:
            return False

        try:
            # Generate target words
            self.target_words = self.word_generator.get_random_words(self.word_count)

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
