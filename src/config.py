"""Configuration module for the typing trainer application."""

import importlib.resources
from pathlib import Path

import platformdirs

from src.domain.config.settings import (
    DEFAULT_SETTINGS,
    THEME_CONFIGS,
    ApplicationSettings,
    ThemeName,
    get_theme_colors,
)

# Application paths
DATA_DIR = Path(platformdirs.user_data_dir("termtypr"))
DATA_DIR.mkdir(parents=True, exist_ok=True)

# User data files (stored in user's data directory)
RECORDS_FILE = DATA_DIR / "history.json"

# Bundled resource files (stored in package, read-only)
# These use importlib.resources to work correctly when packaged
WORDS_FILE = Path(
    importlib.resources.files("src.data.resources").joinpath("words.json")
)

# For backward compatibility, keep APP_ROOT pointing to src directory
APP_ROOT = Path(__file__).parent

# Settings instance with paths
SETTINGS: ApplicationSettings = DEFAULT_SETTINGS.with_paths(
    data_dir=DATA_DIR, words_file=WORDS_FILE, history_file=RECORDS_FILE
)

# Backward compatibility: Legacy dict-based DEFAULT_SETTINGS
DEFAULT_SETTINGS_DICT: dict = {
    "word_count": SETTINGS.game.default_word_count,
    "test_duration": SETTINGS.game.test_duration,
    "theme": SETTINGS.default_theme,
}

# Backward compatibility: Legacy THEMES dict
THEMES = {
    "default": {
        "background": THEME_CONFIGS[ThemeName.DEFAULT].background,
        "text": THEME_CONFIGS[ThemeName.DEFAULT].text,
        "current_word": THEME_CONFIGS[ThemeName.DEFAULT].current_word,
        "correct": THEME_CONFIGS[ThemeName.DEFAULT].correct,
        "incorrect": THEME_CONFIGS[ThemeName.DEFAULT].incorrect,
        "info": THEME_CONFIGS[ThemeName.DEFAULT].info,
    },
    "light": {
        "background": THEME_CONFIGS[ThemeName.LIGHT].background,
        "text": THEME_CONFIGS[ThemeName.LIGHT].text,
        "current_word": THEME_CONFIGS[ThemeName.LIGHT].current_word,
        "correct": THEME_CONFIGS[ThemeName.LIGHT].correct,
        "incorrect": THEME_CONFIGS[ThemeName.LIGHT].incorrect,
        "info": THEME_CONFIGS[ThemeName.LIGHT].info,
    },
}

__all__ = [
    "SETTINGS",
    "DEFAULT_SETTINGS_DICT",
    "THEMES",
    "APP_ROOT",
    "DATA_DIR",
    "WORDS_FILE",
    "RECORDS_FILE",
    "ApplicationSettings",
    "ThemeName",
    "get_theme_colors",
]
