"""Type-safe application settings using Pydantic."""

from enum import Enum
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class ThemeName(str, Enum):
    """Available theme names."""

    DEFAULT = "default"
    LIGHT = "light"


class ThemeColors(BaseModel):
    """Color configuration for a theme."""

    background: str = Field(..., description="Background color")
    text: str = Field(..., description="Text color")
    current_word: str = Field(..., description="Current word highlight color")
    correct: str = Field(..., description="Correct text color")
    incorrect: str = Field(..., description="Incorrect text color")
    info: str = Field(..., description="Info text color")

    model_config = {"frozen": True}  # Make immutable


class GameSettings(BaseModel):
    """Settings for game configuration."""

    default_word_count: int = Field(
        default=20,
        ge=5,
        le=100,
        description="Default number of words for random word games",
    )
    min_word_count: int = Field(
        default=5, ge=1, le=50, description="Minimum allowed word count"
    )
    max_word_count: int = Field(
        default=100, ge=10, le=500, description="Maximum allowed word count"
    )
    test_duration: int = Field(
        default=60, ge=10, le=300, description="Test duration in seconds"
    )

    @field_validator("min_word_count", "max_word_count")
    @classmethod
    def validate_min_max_word_count(cls, v, info):
        """Ensure min is less than max."""
        field_name = info.field_name
        data = info.data

        if field_name == "min_word_count":
            if "max_word_count" in data and v >= data["max_word_count"]:
                raise ValueError("min_word_count must be less than max_word_count")
        elif field_name == "max_word_count":
            if "min_word_count" in data and data["min_word_count"] >= v:
                raise ValueError("min_word_count must be less than max_word_count")

        return v

    model_config = {"frozen": True}


class ApplicationSettings(BaseModel):
    """Main application settings.
    
    FIXME
    """

    # Application info
    app_name: str = Field(default="TermTypr", description="Application name")
    version: str = Field(default="0.4.0", description="Application version")

    # Theme settings
    default_theme: ThemeName = Field(
        default=ThemeName.DEFAULT, description="Default theme to use"
    )

    # Game settings
    game: GameSettings = Field(
        default_factory=GameSettings, description="Game configuration"
    )

    # Paths (computed at runtime)
    data_dir: Optional[Path] = Field(default=None, description="Data directory path")
    words_file: Optional[Path] = Field(default=None, description="Words file path")
    history_file: Optional[Path] = Field(default=None, description="History file path")

    model_config = {
        "frozen": True,
        "use_enum_values": True,  # Use enum values instead of enum objects
    }

    def with_paths(
        self, data_dir: Path, words_file: Path, history_file: Path
    ) -> "ApplicationSettings":
        """Create new settings with paths set."""
        return ApplicationSettings(
            app_name=self.app_name,
            version=self.version,
            default_theme=self.default_theme,
            game=self.game,
            data_dir=data_dir,
            words_file=words_file,
            history_file=history_file,
        )


# Theme configurations
THEME_CONFIGS = {
    ThemeName.DEFAULT: ThemeColors(
        background="black",
        text="white",
        current_word="cyan",
        correct="green",
        incorrect="red",
        info="yellow",
    ),
    ThemeName.LIGHT: ThemeColors(
        background="white",
        text="black",
        current_word="blue",
        correct="green",
        incorrect="red",
        info="magenta",
    ),
}


# Default settings instance
DEFAULT_SETTINGS = ApplicationSettings()


def get_theme_colors(theme_name: ThemeName = ThemeName.DEFAULT) -> ThemeColors:
    """Get theme colors for a given theme name.

    Args:
        theme_name: The theme to get colors for

    Returns:
        ThemeColors configuration

    Raises:
        KeyError: If theme name is not found
    """
    return THEME_CONFIGS[theme_name]
