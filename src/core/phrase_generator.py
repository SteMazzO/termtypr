"""Phrase generator for typing practice."""

import json
import random
from pathlib import Path


class PhraseGenerator:
    """Generates phrases and quotes for typing practice."""

    def __init__(self):
        """Initialize the phrase generator."""
        self.phrases_file = (
            Path(__file__).parent.parent.parent / "data" / "phrases.json"
        )
        self._phrases = self._load_phrases()

    def _load_phrases(self) -> list[str]:
        """Load phrases from the JSON file."""
        try:
            with open(self.phrases_file, encoding="utf-8") as f:
                data = json.load(f)
                return data.get("phrases", [])
        except (FileNotFoundError, json.JSONDecodeError, KeyError):
            print(
                f"Error loading phrases from {self.phrases_file}. Using default phrases."
            )
            return [
                "Type this sample text for practice.",
                "The quick brown fox jumps over the lazy dog.",
                "A journey of a thousand miles begins with a single step.",
                "To be or not to be, that is the question.",
                "All that glitters is not gold.",
            ]

    def get_random_phrase(self) -> str:
        """Get a single random phrase."""
        if not self._phrases:
            return "Type this sample text for practice."
        return random.choice(self._phrases)

    def get_phrases_count(self) -> int:
        """Get the total number of available phrases."""
        return len(self._phrases)
