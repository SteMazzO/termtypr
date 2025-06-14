"""Games package for typing practice mini-games."""

from .base_game import BaseGame
from .phrase_typing_game import PhraseTypingGame
from .random_words_game import RandomWordsGame

__all__ = ["BaseGame", "RandomWordsGame", "PhraseTypingGame"]
