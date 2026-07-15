"""User-configurable preferences that persist between sessions."""

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

# Word count boundaries (used for validation in UserPreferences / UI)
MIN_WORD_COUNT: int = 5
MAX_WORD_COUNT: int = 200
DEFAULT_WORD_COUNT: int = 20

# Ghost setting boundaries (used for validation in UserPreferences / UI)
MIN_GHOST_WPM_THRESHOLD: float = 0.0
MAX_GHOST_WPM_THRESHOLD: float = 500.0
MIN_GHOSTS_TOTAL: int = 1
MAX_GHOSTS_TOTAL: int = 1000

# Rough on-disk size of one saved ghost run, for the settings UI estimate
GHOST_RUN_SIZE_KB: int = 9


class GhostSaveMode(str, Enum):
    """When a completed phrase run is saved as a ghost."""

    ALWAYS_ASK = "ask"
    NEVER = "never"
    AUTO_BEST = "auto_best"
    AUTO_THRESHOLD = "threshold"


class UserPreferences(BaseModel):
    """Mutable user preferences, persisted to disk between sessions."""

    # Runtime mutations (settings dialogs, tests) go through validation
    # too, so enum fields stay enums and bounds always hold.
    model_config = ConfigDict(validate_assignment=True)

    word_count: int = Field(
        default=DEFAULT_WORD_COUNT,
        ge=MIN_WORD_COUNT,
        le=MAX_WORD_COUNT,
        description="Number of words per game",
    )
    ghost_save_mode: GhostSaveMode = Field(
        default=GhostSaveMode.AUTO_BEST,
        description="When to save a completed phrase run as a ghost",
    )
    ghost_wpm_threshold: float = Field(
        default=60.0,
        ge=MIN_GHOST_WPM_THRESHOLD,
        le=MAX_GHOST_WPM_THRESHOLD,
        description="Minimum WPM to save a ghost in threshold mode",
    )
    ghost_min_accuracy: float = Field(
        default=85.0,
        ge=0.0,
        le=100.0,
        description="Minimum accuracy for any automatic ghost save",
    )
    max_ghosts_total: int = Field(
        default=100,
        ge=MIN_GHOSTS_TOTAL,
        le=MAX_GHOSTS_TOTAL,
        description="Global cap on saved ghosts; worst runs are pruned",
    )
