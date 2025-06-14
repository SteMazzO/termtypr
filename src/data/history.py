"""Module for handling typing test records and statistics

Note:
    This implementation loads and rewrites the entire history file for each read and
    write operation. As a result, performance may degrade significantly with very
    large datasets (e.g., millions of records). For large-scale or high-frequency usage,
    consider using a more efficient storage solution or caching mechanism.
"""

import json
import os
from datetime import datetime
import platformdirs


class HistoryManager:
    """Class responsible for managing typing test records."""

    def __init__(self, history_file: str = None):
        """Initialize the HistoryManager.

        Args:
            history_file: Path to the records JSON file. If None, uses default location.
        """
        if history_file:
            self.records_file = history_file
        else:
            # Use platformdirs to get the appropriate user data directory
            data_dir = platformdirs.user_data_dir("termtypr")
            # Create the directory if it doesn't exist
            os.makedirs(data_dir, exist_ok=True)
            self.records_file = os.path.join(data_dir, "history.json")
            # Create empty history file if it doesn't exist
            if not os.path.exists(self.records_file):
                self._initialize_history_file()

    def _initialize_history_file(self):
        """Initialize an empty history file."""
        with open(self.records_file, "w", encoding="utf-8") as f:
            json.dump({"history": []}, f)

    def get_history(self) -> list[dict]:
        """Get all typing history.

        Returns:
            List of record dictionaries.
        """
        try:
            with open(self.records_file, encoding="utf-8") as f:
                data = json.load(f)
                return data.get("history", [])
        except (json.JSONDecodeError, FileNotFoundError) as e:
            print(f"Error loading records: {e}")
            return []

    def add_to_history(
        self, wpm: float, accuracy: float, duration: int, game: str
    ) -> bool:
        """Add a new typing test to history.

        Args:
            wpm: Words per minute.
            accuracy: Typing accuracy percentage.
            duration: Test duration in seconds.
            game: Name of the game or test.

        Returns:
            True if successful, False otherwise.
        """
        try:
            history = self.get_history()

            # Create new record
            new = {
                "date": datetime.now().isoformat(),
                "wpm": wpm,
                "accuracy": accuracy,
                "duration": duration,
                "game": game,
            }

            history.append(new)

            with open(self.records_file, "w", encoding="utf-8") as f:
                json.dump({"history": history}, f, indent=2)
            return True
        except Exception as e:  # noqa
            print(f"Error adding typing test to history: {e}")
            return False

    def get_best_record(self) -> dict:
        """Get the best typing test record based on WPM.

        Returns:
            Dictionary of the best record or None if no records exist.
        """
        history = self.get_history()
        if not history:
            return {}

        return max(history, key=lambda x: x.get("wpm", 0))
