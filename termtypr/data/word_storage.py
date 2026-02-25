"""Module for handling word storage and retrieval for typing tests."""

import json
import logging
from pathlib import Path

from termtypr.config import WORDS_FILE

logger = logging.getLogger(__name__)


class WordStorage:
    """Class responsible for managing word data for typing tests."""

    def __init__(self, words_file: str | Path | None = None):
        """Initialize the WordStorage.

        Args:
            words_file: Path to the words JSON file. Defaults to config.WORDS_FILE.
        """
        self.words_file = Path(words_file) if words_file else WORDS_FILE

    def get_words(self) -> list[str]:
        """Get all words from the storage.

        Returns:
            List of words.

        Raises:
            json.JSONDecodeError: If the words file contains invalid JSON.
        """
        try:
            with open(self.words_file, encoding="utf-8") as f:
                data = json.load(f)
                return data.get("words", [])
        except FileNotFoundError:
            return []

    def add_words(self, new_words: list[str]) -> bool:
        """Add new words to the storage.

        Args:
            new_words: List of words to add.

        Returns:
            True if successful, False otherwise.
        """
        try:
            current_words = self.get_words()
            # Add only unique words
            updated_words = list(dict.fromkeys(current_words + new_words))

            with open(self.words_file, "w", encoding="utf-8") as f:
                json.dump({"words": updated_words}, f, indent=2)
            return True
        except (OSError, json.JSONDecodeError) as e:
            logger.warning("Error adding words: %s", e)
            return False
