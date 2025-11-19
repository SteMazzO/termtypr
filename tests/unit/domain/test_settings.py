"""Tests for Pydantic settings."""

from pathlib import Path

import pytest
from pydantic import ValidationError

from src.domain.config.settings import (
    THEME_CONFIGS,
    ApplicationSettings,
    GameSettings,
    ThemeColors,
    ThemeName,
    get_theme_colors,
)


def test_theme_colors_immutable():
    """Test that ThemeColors is immutable."""
    colors = ThemeColors(
        background="black",
        text="white",
        current_word="cyan",
        correct="green",
        incorrect="red",
        info="yellow",
    )

    with pytest.raises(ValidationError):
        colors.background = "white"  # Should fail - immutable


def test_game_settings_default_values():
    """Test default game settings."""
    settings = GameSettings()

    assert settings.default_word_count == 20
    assert settings.min_word_count == 5
    assert settings.max_word_count == 100
    assert settings.test_duration == 60


def test_game_settings_validation():
    """Test game settings validation."""
    # Valid settings
    settings = GameSettings(default_word_count=30, min_word_count=10, max_word_count=50)
    assert settings.default_word_count == 30

    # Invalid: word count out of range
    with pytest.raises(ValidationError):
        GameSettings(default_word_count=200)  # Exceeds max of 100

    with pytest.raises(ValidationError):
        GameSettings(default_word_count=2)  # Below min of 5


def test_game_settings_min_max_validation():
    """Test that min must be less than max."""
    # Use values that pass field constraints but fail custom validation
    with pytest.raises(ValidationError, match="min_word_count must be less than"):
        GameSettings(min_word_count=30, max_word_count=20)


def test_application_settings_defaults():
    """Test default application settings."""
    settings = ApplicationSettings()

    assert settings.app_name == "TermTypr"
    assert settings.version == "0.4.0"
    assert settings.default_theme == ThemeName.DEFAULT
    assert settings.game.default_word_count == 20


def test_application_settings_immutable():
    """Test that ApplicationSettings is immutable."""
    settings = ApplicationSettings()

    with pytest.raises(ValidationError):
        settings.app_name = "NewName"  # Should fail - immutable


def test_application_settings_with_paths():
    """Test setting paths on application settings."""
    settings = ApplicationSettings()

    data_dir = Path("/tmp/data")
    words_file = Path("/tmp/data/words.json")
    history_file = Path("/tmp/data/history.json")

    new_settings = settings.with_paths(data_dir, words_file, history_file)

    assert new_settings.data_dir == data_dir
    assert new_settings.words_file == words_file
    assert new_settings.history_file == history_file
    # Original unchanged
    assert settings.data_dir is None


def test_theme_configs_exist():
    """Test that theme configurations are defined."""
    assert ThemeName.DEFAULT in THEME_CONFIGS
    assert ThemeName.LIGHT in THEME_CONFIGS

    default_theme = THEME_CONFIGS[ThemeName.DEFAULT]
    assert isinstance(default_theme, ThemeColors)
    assert default_theme.background == "black"

    light_theme = THEME_CONFIGS[ThemeName.LIGHT]
    assert isinstance(light_theme, ThemeColors)
    assert light_theme.background == "white"


def test_get_theme_colors():
    """Test getting theme colors by name."""
    default_colors = get_theme_colors(ThemeName.DEFAULT)
    assert default_colors.background == "black"
    assert default_colors.correct == "green"

    light_colors = get_theme_colors(ThemeName.LIGHT)
    assert light_colors.background == "white"


def test_get_theme_colors_default():
    """Test getting theme colors with default."""
    colors = get_theme_colors()
    assert colors == THEME_CONFIGS[ThemeName.DEFAULT]


def test_custom_game_settings():
    """Test creating custom game settings."""
    settings = GameSettings(
        default_word_count=50,
        min_word_count=10,
        max_word_count=200,
        test_duration=120,
    )

    assert settings.default_word_count == 50
    assert settings.min_word_count == 10
    assert settings.max_word_count == 200
    assert settings.test_duration == 120


def test_custom_application_settings():
    """Test creating custom application settings."""
    custom_game = GameSettings(default_word_count=30)

    settings = ApplicationSettings(
        app_name="CustomTypr",
        version="1.0.0",
        default_theme=ThemeName.LIGHT,
        game=custom_game,
    )

    assert settings.app_name == "CustomTypr"
    assert settings.version == "1.0.0"
    assert settings.default_theme == ThemeName.LIGHT
    assert settings.game.default_word_count == 30
