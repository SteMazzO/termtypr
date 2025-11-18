"""Module for handling word storage and retrieval for typing tests"""

import importlib.resources
import json


class WordStorage:
    """Class responsible for managing word data for typing tests."""

    def __init__(self, words_file: str = None):
        """Initialize the WordStorage.

        Args:
            words_file: Path to the words JSON file.
        """
        if words_file:
            self.words_file = words_file
        else:
            # Use package resources to access data files
            self.words_file = str(
                importlib.resources.files("src.data.resources").joinpath("words.json")
            )

    def get_words(self) -> list[str]:
        """Get all words from the storage.

        Returns:
            List of words.
        """
        try:
            with open(self.words_file, encoding="utf-8") as f:
                data = json.load(f)
                return data.get("words", [])
        except (json.JSONDecodeError, FileNotFoundError) as e:
            print(f"Error loading words: {e}")
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
            updated_words = list(set(current_words + new_words))

            with open(self.words_file, "w", encoding="utf-8") as f:
                json.dump({"words": updated_words}, f, indent=2)
            return True
        except Exception as e:
            print(f"Error adding words: {e}")
            return False
