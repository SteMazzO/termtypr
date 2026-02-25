"""User-configurable preferences that persist between sessions."""

from pydantic import BaseModel, Field

# Word count boundaries (used for validation in UserPreferences / UI)
MIN_WORD_COUNT: int = 5
MAX_WORD_COUNT: int = 200
DEFAULT_WORD_COUNT: int = 20


class UserPreferences(BaseModel):
    """Mutable user preferences, persisted to disk between sessions."""

    word_count: int = Field(
        default=DEFAULT_WORD_COUNT,
        ge=MIN_WORD_COUNT,
        le=MAX_WORD_COUNT,
        description="Number of words per game",
    )
