"""Configuration module for the typing trainer application."""

from pathlib import Path

# Application paths
APP_ROOT = Path(__file__).parent.parent
DATA_DIR = APP_ROOT / "data"
WORDS_FILE = DATA_DIR / "words.json"
RECORDS_FILE = DATA_DIR / "history.json"

# Default settings
DEFAULT_SETTINGS: dict = {
    "word_count": 20,
    "test_duration": 60,  # seconds
    "theme": "default",
}

# Theme colors
THEMES = {
    "default": {
        "background": "black",
        "text": "white",
        "current_word": "cyan",
        "correct": "green",
        "incorrect": "red",
        "info": "yellow",
    },
    "light": {
        "background": "white",
        "text": "black",
        "current_word": "blue",
        "correct": "green",
        "incorrect": "red",
        "info": "magenta",
    },
}

# Make sure data directory exists
DATA_DIR.mkdir(parents=True, exist_ok=True)
