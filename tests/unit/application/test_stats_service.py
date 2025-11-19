"""Tests for StatsService."""

from datetime import datetime, timedelta

import pytest

from src.application.services.stats_service import StatsService
from src.domain.models.game_result import GameResult
from src.domain.models.typing_stats import TypingStats
from src.infrastructure.persistence.memory_history_repository import (
    InMemoryHistoryRepository,
)


@pytest.fixture
def repository():
    """Create a memory repository for testing."""
    return InMemoryHistoryRepository()


@pytest.fixture
def service(repository):
    """Create a stats service with memory repository."""
    return StatsService(repository)


@pytest.fixture
def sample_result():
    """Create a sample game result."""
    return GameResult(
        game_type="Random Words",
        wpm=60.0,
        accuracy=95.0,
        duration=30.0,
        total_characters=150,
        correct_characters=142,
        error_count=8,
        timestamp=datetime.now(),
        is_new_record=False,
    )


@pytest.fixture
def populated_service(repository, service):
    """Create a service with some history."""
    base_time = datetime.now()

    # Add multiple results with varying stats
    results = [
        GameResult(
            game_type="Random Words",
            wpm=50.0,
            accuracy=90.0,
            duration=30.0,
            total_characters=125,
            correct_characters=112,
            error_count=13,
            timestamp=base_time - timedelta(days=5),
            is_new_record=False,
        ),
        GameResult(
            game_type="Random Words",
            wpm=60.0,
            accuracy=95.0,
            duration=30.0,
            total_characters=150,
            correct_characters=142,
            error_count=8,
            timestamp=base_time - timedelta(days=4),
            is_new_record=False,
        ),
        GameResult(
            game_type="Phrase Typing",
            wpm=70.0,
            accuracy=98.0,
            duration=30.0,
            total_characters=175,
            correct_characters=171,
            error_count=4,
            timestamp=base_time - timedelta(days=3),
            is_new_record=True,
        ),
        GameResult(
            game_type="Random Words",
            wpm=55.0,
            accuracy=92.0,
            duration=30.0,
            total_characters=137,
            correct_characters=126,
            error_count=11,
            timestamp=base_time - timedelta(days=2),
            is_new_record=False,
        ),
        GameResult(
            game_type="Phrase Typing",
            wpm=65.0,
            accuracy=96.0,
            duration=30.0,
            total_characters=162,
            correct_characters=155,
            error_count=7,
            timestamp=base_time - timedelta(days=1),
            is_new_record=False,
        ),
    ]

    for result in results:
        repository.save(result)

    return service


class TestStatsServiceInitialization:
    """Tests for service initialization."""

    def test_initialization_with_repository(self, repository):
        """Test service can be initialized with a repository."""
        service = StatsService(repository)
        assert service.history_repository is repository

    def test_initialization_stores_repository(self, service, repository):
        """Test initialized service stores the repository."""
        assert service.history_repository is repository


class TestCalculateStatsFromResult:
    """Tests for converting GameResult to TypingStats."""

    def test_calculate_stats_from_result(self, service, sample_result):
        """Test converting a game result to typing stats."""
        stats = service.calculate_stats_from_result(sample_result)

        assert isinstance(stats, TypingStats)
        assert stats.wpm == sample_result.wpm
        assert stats.accuracy == sample_result.accuracy
        assert stats.duration == sample_result.duration
        assert stats.total_characters == sample_result.total_characters
        assert stats.correct_characters == sample_result.correct_characters
        assert stats.error_count == sample_result.error_count

    def test_calculate_stats_handles_none_values(self, service):
        """Test converting result with None values."""
        result = GameResult(
            game_type="Test",
            wpm=50.0,
            accuracy=90.0,
            duration=30.0,
            timestamp=datetime.now(),
            is_new_record=False,
        )

        stats = service.calculate_stats_from_result(result)

        assert stats.total_characters == 0
        assert stats.correct_characters == 0
        assert stats.error_count == 0


class TestGetBestPerformance:
    """Tests for retrieving best performance."""

    def test_get_best_performance_with_empty_history(self, service):
        """Test getting best performance from empty history."""
        best = service.get_best_performance()
        assert best is None

    def test_get_best_performance_returns_highest_wpm(self, populated_service):
        """Test best performance returns result with highest WPM."""
        best = populated_service.get_best_performance()

        assert best is not None
        assert abs(best.wpm - 70.0) < 0.01
        assert best.game_type == "Phrase Typing"


class TestGetRecentResults:
    """Tests for retrieving recent results."""

    def test_get_recent_results_with_empty_history(self, service):
        """Test getting recent results from empty history."""
        results = service.get_recent_results()
        assert results == []

    def test_get_recent_results_default_limit(self, populated_service):
        """Test getting recent results with default limit."""
        results = populated_service.get_recent_results()
        assert len(results) == 5  # We only have 5 results

    def test_get_recent_results_custom_limit(self, populated_service):
        """Test getting recent results with custom limit."""
        results = populated_service.get_recent_results(limit=3)
        assert len(results) == 3

    def test_get_recent_results_ordered_by_time(self, populated_service):
        """Test recent results are ordered newest first."""
        results = populated_service.get_recent_results()

        for i in range(len(results) - 1):
            assert results[i].timestamp >= results[i + 1].timestamp


class TestGetAllResults:
    """Tests for retrieving all results."""

    def test_get_all_results_with_empty_history(self, service):
        """Test getting all results from empty history."""
        results = service.get_all_results()
        assert results == []

    def test_get_all_results_returns_all(self, populated_service):
        """Test getting all results returns everything."""
        results = populated_service.get_all_results()
        assert len(results) == 5

    def test_get_all_results_ordered_by_time(self, populated_service):
        """Test all results are ordered newest first."""
        results = populated_service.get_all_results()

        for i in range(len(results) - 1):
            assert results[i].timestamp >= results[i + 1].timestamp


class TestCalculateAverageStats:
    """Tests for calculating average statistics."""

    def test_calculate_average_stats_with_empty_history(self, service):
        """Test calculating averages from empty history."""
        avg = service.calculate_average_stats()
        assert avg is None

    def test_calculate_average_stats_all_results(self, populated_service):
        """Test calculating averages from all results."""
        avg = populated_service.calculate_average_stats()

        assert avg is not None
        assert isinstance(avg, TypingStats)
        # Average WPM: (50 + 60 + 70 + 55 + 65) / 5 = 60.0
        assert abs(avg.wpm - 60.0) < 0.01
        # Average accuracy: (90 + 95 + 98 + 92 + 96) / 5 = 94.2
        assert abs(avg.accuracy - 94.2) < 0.01

    def test_calculate_average_stats_with_limit(self, populated_service):
        """Test calculating averages from limited results."""
        avg = populated_service.calculate_average_stats(limit=3)

        assert avg is not None
        # Should use 3 most recent: 65, 55, 70
        # Average: (65 + 55 + 70) / 3 = 63.33...
        assert abs(avg.wpm - 63.33) < 0.01


class TestGetProgressSummary:
    """Tests for progress summary generation."""

    def test_get_progress_summary_with_empty_history(self, service):
        """Test progress summary with no history."""
        summary = service.get_progress_summary()

        assert summary["total_games"] == 0
        assert abs(summary["average_wpm"] - 0.0) < 0.01
        assert abs(summary["best_wpm"] - 0.0) < 0.01
        assert abs(summary["recent_average_wpm"] - 0.0) < 0.01
        assert abs(summary["improvement"] - 0.0) < 0.01

    def test_get_progress_summary_with_results(self, populated_service):
        """Test progress summary with results."""
        summary = populated_service.get_progress_summary(recent_count=3)

        assert summary["total_games"] == 5
        assert abs(summary["average_wpm"] - 60.0) < 0.01
        assert abs(summary["best_wpm"] - 70.0) < 0.01
        assert abs(summary["recent_average_wpm"] - 63.33) < 0.01
        assert "improvement" in summary
        assert "total_time_spent" in summary

    def test_get_progress_summary_calculates_improvement(self, populated_service):
        """Test progress summary calculates improvement correctly."""
        summary = populated_service.get_progress_summary(recent_count=2)

        # Recent 2: 65, 55 = avg 60.0
        # Older 3: 70, 60, 50 = avg 60.0
        # Improvement: 60 - 60 = 0
        assert abs(summary["improvement"]) < 0.01

    def test_get_progress_summary_no_improvement_calculation_when_insufficient_data(
        self, service, repository
    ):
        """Test no improvement calculation when not enough results."""
        # Add only 2 results
        for i in range(2):
            repository.save(
                GameResult(
                    game_type="Test",
                    wpm=50.0 + i * 10,
                    accuracy=90.0,
                    duration=30.0,
                    total_characters=100,
                    correct_characters=90,
                    error_count=10,
                    timestamp=datetime.now() - timedelta(days=i),
                    is_new_record=False,
                )
            )

        summary = service.get_progress_summary(recent_count=10)
        # Not enough data to calculate improvement (need more than recent_count)
        assert abs(summary["improvement"] - 0.0) < 0.01


class TestFormatResultSummary:
    """Tests for formatting result summaries."""

    def test_format_result_summary_basic(self, service, sample_result):
        """Test formatting a basic result summary."""
        summary = service.format_result_summary(sample_result)

        assert "Game: Random Words" in summary
        assert "WPM: 60.0" in summary
        assert "Accuracy: 95.0%" in summary
        assert "Duration: 30.0s" in summary

    def test_format_result_summary_with_record(self, service):
        """Test formatting a record result summary."""
        result = GameResult(
            game_type="Test",
            wpm=100.0,
            accuracy=99.0,
            duration=30.0,
            timestamp=datetime.now(),
            is_new_record=True,
        )

        summary = service.format_result_summary(result)

        assert "🏆 NEW RECORD!" in summary


class TestFormatStatsTable:
    """Tests for formatting stats tables."""

    def test_format_stats_table_with_empty_history(self, service):
        """Test formatting table with no history."""
        table = service.format_stats_table()
        assert table == []

    def test_format_stats_table_structure(self, populated_service):
        """Test formatted table has correct structure."""
        table = populated_service.format_stats_table(limit=3)

        assert len(table) == 3

        for row in table:
            assert "rank" in row
            assert "date" in row
            assert "game" in row
            assert "wpm" in row
            assert "accuracy" in row
            assert "duration" in row
            assert "record" in row

    def test_format_stats_table_ordering(self, populated_service):
        """Test table rows are ordered correctly."""
        table = populated_service.format_stats_table()

        for idx, row in enumerate(table, 1):
            assert row["rank"] == idx

    def test_format_stats_table_record_marker(self, populated_service):
        """Test record marker appears in table."""
        table = populated_service.format_stats_table()

        # Find the record entry (should be the one with WPM 70.0)
        record_entries = [row for row in table if row["record"] == "🏆"]
        assert len(record_entries) == 1
        assert record_entries[0]["wpm"] == "70.0"


class TestGetGameTypeStats:
    """Tests for game type statistics."""

    def test_get_game_type_stats_with_empty_history(self, service):
        """Test game type stats with no history."""
        stats = service.get_game_type_stats()
        assert stats == {}

    def test_get_game_type_stats_groups_by_type(self, populated_service):
        """Test stats are grouped by game type."""
        stats = populated_service.get_game_type_stats()

        assert "Random Words" in stats
        assert "Phrase Typing" in stats

    def test_get_game_type_stats_calculates_correctly(self, populated_service):
        """Test game type stats are calculated correctly."""
        stats = populated_service.get_game_type_stats()

        random_words_stats = stats["Random Words"]
        assert random_words_stats["games_played"] == 3
        # WPMs: 50, 60, 55 -> avg 55.0, best 60.0
        assert abs(random_words_stats["average_wpm"] - 55.0) < 0.01
        assert abs(random_words_stats["best_wpm"] - 60.0) < 0.01
        # Accuracies: 90, 95, 92 -> avg 92.33
        assert abs(random_words_stats["average_accuracy"] - 92.33) < 0.01

        phrase_stats = stats["Phrase Typing"]
        assert phrase_stats["games_played"] == 2
        # WPMs: 70, 65 -> avg 67.5, best 70.0
        assert abs(phrase_stats["average_wpm"] - 67.5) < 0.01
        assert abs(phrase_stats["best_wpm"] - 70.0) < 0.01


class TestClearHistory:
    """Tests for clearing history."""

    def test_clear_history_with_empty_repository(self, service):
        """Test clearing empty history."""
        result = service.clear_history()
        assert result is True

    def test_clear_history_removes_all_results(self, populated_service, repository):
        """Test clearing history removes all results."""
        # Verify we have results
        assert len(repository.get_all()) > 0

        # Clear history
        result = populated_service.clear_history()

        assert result is True
        assert len(repository.get_all()) == 0

    def test_clear_history_via_service(self, populated_service):
        """Test clearing history through service methods."""
        # Clear
        populated_service.clear_history()

        # Verify through service methods
        assert populated_service.get_all_results() == []
        assert populated_service.get_best_performance() is None
        assert populated_service.calculate_average_stats() is None
