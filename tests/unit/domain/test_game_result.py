"""Tests for GameResult domain model."""

from datetime import datetime, timezone

from termtypr.domain.models.game_result import GameResult


class TestFromDictLegacyKeys:
    """Tests for from_dict() backward-compatible key handling."""

    def test_legacy_game_key_maps_to_game_type(self):
        """'game' key in old records maps to game_type."""
        data = {
            "wpm": 75.0,
            "accuracy": 95.0,
            "duration": 30.0,
            "game": "Phrase Typing",
            "date": "2025-11-20T17:00:16.590143",
        }
        result = GameResult.from_dict(data)
        assert result.game_type == "Phrase Typing"

    def test_legacy_date_key_maps_to_timestamp(self):
        """'date' key in old records maps to timestamp."""
        data = {
            "wpm": 80.0,
            "accuracy": 97.0,
            "duration": 20.0,
            "game": "Random Words",
            "date": "2025-12-01T10:30:00.000000",
        }
        result = GameResult.from_dict(data)
        assert result.timestamp.year == 2025
        assert result.timestamp.month == 12
        assert result.timestamp.day == 1

    def test_new_keys_take_precedence(self):
        """Modern keys (game_type, timestamp) are used when present."""
        data = {
            "wpm": 90.0,
            "accuracy": 98.0,
            "duration": 15.0,
            "game_type": "Random Words",
            "timestamp": "2026-01-15T12:00:00+00:00",
        }
        result = GameResult.from_dict(data)
        assert result.game_type == "Random Words"
        assert result.timestamp.tzinfo is not None

    def test_missing_game_key_defaults_to_unknown(self):
        """Missing both 'game' and 'game_type' falls back to 'Unknown'."""
        data = {
            "wpm": 60.0,
            "accuracy": 90.0,
            "duration": 25.0,
            "date": "2025-11-20T10:00:00",
        }
        result = GameResult.from_dict(data)
        assert result.game_type == "Unknown"


class TestFromDictTimezoneNormalization:
    """Tests for naive-to-UTC timestamp normalization."""

    def test_naive_timestamp_gets_utc(self):
        """Naive datetime strings are normalised to UTC."""
        data = {
            "wpm": 70.0,
            "accuracy": 92.0,
            "duration": 30.0,
            "game_type": "Phrase Typing",
            "timestamp": "2025-11-20T17:00:16.590143",
        }
        result = GameResult.from_dict(data)
        assert result.timestamp.tzinfo == timezone.utc

    def test_aware_timestamp_preserved(self):
        """Timezone-aware timestamps keep their original tzinfo."""
        data = {
            "wpm": 88.0,
            "accuracy": 98.0,
            "duration": 10.0,
            "game_type": "Random Words",
            "timestamp": "2026-02-24T11:33:31.376517+00:00",
        }
        result = GameResult.from_dict(data)
        assert result.timestamp.tzinfo is not None
        assert result.timestamp.hour == 11

    def test_missing_timestamp_defaults_to_utc_now(self):
        """Missing timestamp falls back to current UTC time."""
        data = {
            "wpm": 50.0,
            "accuracy": 85.0,
            "duration": 40.0,
            "game_type": "Phrase Typing",
        }
        result = GameResult.from_dict(data)
        assert result.timestamp.tzinfo is not None
        # Should be very recent (within the last second)
        delta = datetime.now(tz=timezone.utc) - result.timestamp
        assert delta.total_seconds() < 2


class TestToDict:
    """Tests for to_dict() serialization."""

    def test_round_trip(self):
        """to_dict → from_dict preserves key fields."""
        original = GameResult(
            wpm=82.5,
            accuracy=96.3,
            duration=25.0,
            game_type="Phrase Typing",
            timestamp=datetime(2026, 1, 15, 12, 0, tzinfo=timezone.utc),
            total_characters=150,
            correct_characters=140,
            error_count=5,
        )
        data = original.to_dict()
        restored = GameResult.from_dict(data)

        assert restored.wpm == original.wpm
        assert restored.accuracy == original.accuracy
        assert restored.duration == original.duration
        assert restored.game_type == original.game_type
        assert restored.timestamp == original.timestamp
        assert restored.total_characters == original.total_characters
        assert restored.correct_characters == original.correct_characters
        assert restored.error_count == original.error_count

    def test_transient_fields_excluded(self):
        """is_new_record and previous_best are not serialized."""
        result = GameResult(
            wpm=100.0,
            accuracy=100.0,
            duration=10.0,
            game_type="Random Words",
            timestamp=datetime.now(tz=timezone.utc),
            is_new_record=True,
            previous_best=90.0,
        )
        data = result.to_dict()
        assert "is_new_record" not in data
        assert "previous_best" not in data
