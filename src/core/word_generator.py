"""Module for generating words for typing tests"""

import random

from src.data.word_storage import WordStorage


class WordGenerator:
    """Class responsible for generating word sequences for typing tests."""

    def __init__(self, word_storage: WordStorage = None):
        """Initialize the WordGenerator.

        Args:
            word_storage: WordStorage instance.
        """
        self.word_storage = word_storage or WordStorage()

    def get_random_words(self, count: int = 20) -> list[str]:
        """Get a random selection of words.

        Args:
            count: Number of words to generate.

        Returns:
            List of random words.
        """
        available_words = self.word_storage.get_words()

        if not available_words:
            return []

        # If we have fewer words than requested, repeat some words
        if len(available_words) < count:
            return random.choices(available_words, k=count)

        # Otherwise, select random words without replacement
        return random.sample(available_words, count)
