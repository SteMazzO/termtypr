"""Tests for GameResult domain model."""

from datetime import datetime, timezone

from termtypr.core.phrase_hash import phrase_hash
from termtypr.domain.models.game_result import GameResult


class TestPhraseIdentity:
    """Tests for phrase_text / phrase_hash."""

    def test_phrase_hash_derived_from_text(self):
        """phrase_hash is a stable 16-char digest of phrase_text."""
        result = GameResult(
            wpm=70.0,
            accuracy=95.0,
            duration=20.0,
            game_type="Phrase Typing",
            timestamp=datetime.now(tz=timezone.utc),
            phrase_text="The quick brown fox",
        )
        assert result.phrase_hash == phrase_hash("The quick brown fox")
        assert len(result.phrase_hash) == 16

    def test_phrase_hash_none_without_text(self):
        """Results without a phrase have no phrase_hash."""
        result = GameResult(
            wpm=70.0,
            accuracy=95.0,
            duration=20.0,
            game_type="Random Words",
            timestamp=datetime.now(tz=timezone.utc),
        )
        assert result.phrase_text is None
        assert result.phrase_hash is None
