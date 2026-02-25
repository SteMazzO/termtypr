"""Module for generating words for typing tests."""

import random

from termtypr.data.word_storage import WordStorage


def get_random_words(
    count: int = 20, word_storage: WordStorage | None = None
) -> list[str]:
    """Get a random selection of words.

    Args:
        count: Number of words to generate.
        word_storage: WordStorage instance. Defaults to a new instance.

    Returns:
        List of random words.
    """
    storage = word_storage or WordStorage()
    available_words = storage.get_words()

    if not available_words:
        return []

    # If we have fewer words than requested, repeat some words
    if len(available_words) < count:
        return random.choices(available_words, k=count)

    # Otherwise, select random words without replacement
    return random.sample(available_words, count)
