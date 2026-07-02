"""Module for handling word storage and retrieval for typing tests."""

import json
import logging
from pathlib import Path

from termtypr.config import USER_WORDS_FILE, WORDS_FILE

logger = logging.getLogger(__name__)


class WordStorage:
    """Class responsible for managing word data for typing tests.

    Words come from two sources: the read-only list bundled with the package
    and a user-managed file in the user data directory.
    """

    def __init__(
        self,
        words_file: str | Path | None = None,
        user_words_file: str | Path | None = None,
    ):
        """Initialize the WordStorage.

        Args:
            words_file: Path to the bundled words JSON file.
                Defaults to config.WORDS_FILE.
            user_words_file: Path to the writable user words JSON file.
                Defaults to config.USER_WORDS_FILE.
        """
        self.words_file = Path(words_file) if words_file else WORDS_FILE
        self.user_words_file = (
            Path(user_words_file) if user_words_file else USER_WORDS_FILE
        )

    @staticmethod
    def _read_words(path: Path) -> list[str]:
        """Read a words JSON file, returning an empty list if missing/corrupt."""
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
                return data.get("words", [])
        except FileNotFoundError:
            return []
        except (OSError, json.JSONDecodeError) as e:
            logger.warning("Error reading words from %s: %s", path, e)
            return []

    def get_words(self) -> list[str]:
        """Get all words from the storage (bundled + user-added).

        Returns:
            Deduplicated list of words.
        """
        bundled = self._read_words(self.words_file)
        custom = self._read_words(self.user_words_file)
        return list(dict.fromkeys(bundled + custom))

    def add_words(self, new_words: list[str]) -> bool:
        """Add new words to the user words file.

        Args:
            new_words: List of words to add.

        Returns:
            True if successful, False otherwise.
        """
        try:
            existing = set(self.get_words())
            current_custom = self._read_words(self.user_words_file)
            to_add = [w for w in new_words if w not in existing]
            updated_words = list(dict.fromkeys(current_custom + to_add))

            self.user_words_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.user_words_file, "w", encoding="utf-8") as f:
                json.dump({"words": updated_words}, f, indent=2)
            return True
        except OSError as e:
            logger.warning("Error adding words: %s", e)
            return False
