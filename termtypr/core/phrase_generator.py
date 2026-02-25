"""Phrase generator for typing practice."""

import json
import random
from functools import cache

from termtypr.config import PHRASES_FILE


@cache
def _load_phrases() -> tuple[str, ...]:
    """Load phrases from the JSON file (cached after first call).

    Raises:
        FileNotFoundError: If the phrases file does not exist.
        json.JSONDecodeError: If the file contains invalid JSON.
        ValueError: If the file contains no phrases.
    """
    with open(PHRASES_FILE, encoding="utf-8") as f:
        data = json.load(f)

    phrases = tuple(data.get("phrases", ()))
    if not phrases:
        raise ValueError(f"No phrases found in {PHRASES_FILE}")
    return phrases


def get_random_phrase() -> str:
    """Get a single random phrase."""
    return random.choice(_load_phrases())
