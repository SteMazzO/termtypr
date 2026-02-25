"""Configuration module."""

import importlib.resources
from pathlib import Path

import platformdirs

from termtypr.domain.models.user_preferences import UserPreferences
from termtypr.infrastructure.persistence.json_preferences_repository import (
    JsonPreferencesRepository,
)

# Paths
DATA_DIR = Path(platformdirs.user_data_dir("termtypr"))

RECORDS_FILE = DATA_DIR / "history.json"
PREFERENCES_FILE = DATA_DIR / "preferences.json"

WORDS_FILE = Path(
    importlib.resources.files("termtypr.data.resources").joinpath("words.json")
)
PHRASES_FILE = Path(
    importlib.resources.files("termtypr.data.resources").joinpath("phrases.json")
)

# User preferences (mutable, persisted)
_preferences_repo = JsonPreferencesRepository(PREFERENCES_FILE)
user_preferences: UserPreferences = _preferences_repo.load()


def save_preferences() -> None:
    """Persist the current user_preferences to disk."""
    _preferences_repo.save(user_preferences)
