"""JSON file-based persistence for user preferences."""

import json
import logging
from pathlib import Path

from termtypr.domain.models.user_preferences import UserPreferences

logger = logging.getLogger(__name__)


class JsonPreferencesRepository:
    """Persists user preferences as a JSON file in the user data directory."""

    def __init__(self, file_path: Path) -> None:
        self.file_path = file_path

    def load(self) -> UserPreferences:
        """Load preferences from JSON file, returning defaults if missing or corrupt."""
        if not self.file_path.exists():
            return UserPreferences()

        try:
            data = json.loads(self.file_path.read_text(encoding="utf-8"))
            return UserPreferences(**data)
        except (ValueError, TypeError, OSError) as exc:
            logger.warning(
                "Failed to load preferences from %s: %s", self.file_path, exc
            )
            return UserPreferences()

    def save(self, preferences: UserPreferences) -> None:
        """Save preferences to JSON file."""
        try:
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
            self.file_path.write_text(
                preferences.model_dump_json(indent=2), encoding="utf-8"
            )
        except OSError as exc:
            logger.error("Failed to save preferences to %s: %s", self.file_path, exc)
