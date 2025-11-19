"""Statistics service for calculating and formatting typing statistics."""

from typing import Any, Optional

from src.domain.models.game_result import GameResult
from src.domain.models.typing_stats import TypingStats
from src.domain.repositories.history_repository import HistoryRepository


class StatsService:
    """Service for managing typing statistics and history.

    This service provides business logic for:
    - Calculating statistics from game results
    - Formatting statistics for display
    - Retrieving historical data
    - Computing aggregates and trends
    """

    def __init__(self, history_repository: HistoryRepository):
        """Initialize the stats service.

        Args:
            history_repository: Repository for accessing game history
        """
        self.history_repository = history_repository

    def calculate_stats_from_result(self, result: GameResult) -> TypingStats:
        """Calculate TypingStats from a GameResult.

        Args:
            result: The game result to convert

        Returns:
            TypingStats value object with calculated statistics
        """
        # Estimate word counts from characters (avg 5 chars per word)
        total_chars = result.total_characters or 0
        estimated_words = total_chars // 5

        return TypingStats(
            wpm=result.wpm,
            accuracy=result.accuracy,
            duration=result.duration,
            typed_word_count=estimated_words,
            target_word_count=estimated_words,
            total_characters=total_chars,
            correct_characters=result.correct_characters or 0,
            error_count=result.error_count or 0,
            is_completed=True,
        )

    def get_best_performance(self) -> Optional[GameResult]:
        """Get the best performance from history.

        Returns:
            GameResult with highest WPM, or None if no history
        """
        return self.history_repository.get_best()

    def get_recent_results(
        self, limit: int = 10, sort: str = "desc"
    ) -> list[GameResult]:
        """Get recent game results.

        Args:
            limit: Maximum number of results to return
            sort: Sort order - 'desc' for newest first (default), 'asc' for oldest first

        Returns:
            List of recent GameResult objects
        """
        return self.history_repository.get_recent(limit, sort=sort)

    def get_all_results(self, sort: str = "desc") -> list[GameResult]:
        """Get all game results from history.

        Args:
            sort: Sort order - 'desc' for newest first (default), 'asc' for oldest first

        Returns:
            List of all GameResult objects
        """
        return self.history_repository.get_all(sort=sort)

    def calculate_average_stats(
        self, limit: Optional[int] = None
    ) -> Optional[TypingStats]:
        """Calculate average statistics from recent history.

        Args:
            limit: Number of recent games to include (None for all)

        Returns:
            TypingStats with averaged values, or None if no history
        """
        results = (
            self.get_recent_results(limit, sort="desc")
            if limit
            else self.get_all_results(sort="desc")
        )

        if not results:
            return None

        total_wpm = sum(r.wpm for r in results)
        total_accuracy = sum(r.accuracy for r in results)
        total_duration = sum(r.duration for r in results)
        total_chars = sum(r.total_characters or 0 for r in results)
        total_correct = sum(r.correct_characters or 0 for r in results)
        total_errors = sum(r.error_count or 0 for r in results)

        count = len(results)
        avg_chars = total_chars // count

        return TypingStats(
            wpm=total_wpm / count,
            accuracy=total_accuracy / count,
            duration=total_duration / count,
            typed_word_count=avg_chars // 5,
            target_word_count=avg_chars // 5,
            total_characters=avg_chars,
            correct_characters=total_correct // count,
            error_count=total_errors // count,
            is_completed=True,
        )

    def get_progress_summary(self, recent_count: int = 10) -> dict[str, Any]:
        """Get a summary of typing progress.

        Args:
            recent_count: Number of recent games to analyze

        Returns:
            Dictionary with progress metrics
        """
        all_results = self.get_all_results()
        recent_results = self.get_recent_results(recent_count)
        best = self.get_best_performance()

        if not all_results:
            return {
                "total_games": 0,
                "average_wpm": 0.0,
                "best_wpm": 0.0,
                "recent_average_wpm": 0.0,
                "improvement": 0.0,
            }

        # Calculate overall average
        overall_avg_wpm = sum(r.wpm for r in all_results) / len(all_results)

        # Calculate recent average
        recent_avg_wpm = 0.0
        if recent_results:
            recent_avg_wpm = sum(r.wpm for r in recent_results) / len(recent_results)

        # Calculate improvement
        improvement = 0.0
        if len(all_results) > recent_count:
            older_results = all_results[recent_count:]
            older_avg_wpm = sum(r.wpm for r in older_results) / len(older_results)
            improvement = recent_avg_wpm - older_avg_wpm

        return {
            "total_games": len(all_results),
            "average_wpm": overall_avg_wpm,
            "best_wpm": best.wpm if best else 0.0,
            "recent_average_wpm": recent_avg_wpm,
            "improvement": improvement,
            "total_time_spent": sum(r.duration for r in all_results),
        }

    def format_result_summary(self, result: GameResult) -> str:
        """Format a game result as a summary string.

        Args:
            result: The result to format

        Returns:
            Formatted string representation
        """
        lines = [
            f"Game: {result.game_type}",
            f"WPM: {result.wpm:.1f}",
            f"Accuracy: {result.accuracy:.1f}%",
            f"Duration: {result.duration:.1f}s",
        ]

        if result.is_new_record:
            lines.append("🏆 NEW RECORD!")

        return "\n".join(lines)

    def format_stats_table(self, limit: int = 10) -> list[dict[str, Any]]:
        """Format recent results as a table-ready data structure.

        Args:
            limit: Number of results to include

        Returns:
            List of dictionaries with formatted statistics
        """
        results = self.get_recent_results(limit)

        table_data = []
        for idx, result in enumerate(results, 1):
            table_data.append(
                {
                    "rank": idx,
                    "date": result.timestamp.strftime("%Y-%m-%d %H:%M"),
                    "game": result.game_type,
                    "wpm": f"{result.wpm:.1f}",
                    "accuracy": f"{result.accuracy:.1f}%",
                    "duration": f"{result.duration:.0f}s",
                    "record": "🏆" if result.is_new_record else "",
                }
            )

        return table_data

    def get_game_type_stats(self) -> dict[str, dict[str, float]]:
        """Get statistics broken down by game type.

        Returns:
            Dictionary mapping game type to its statistics
        """
        all_results = self.get_all_results()

        if not all_results:
            return {}

        # Group results by game type
        by_type: dict[str, list[GameResult]] = {}
        for result in all_results:
            if result.game_type not in by_type:
                by_type[result.game_type] = []
            by_type[result.game_type].append(result)

        # Calculate stats for each type
        stats_by_type = {}
        for game_type, results in by_type.items():
            count = len(results)
            stats_by_type[game_type] = {
                "games_played": count,
                "average_wpm": sum(r.wpm for r in results) / count,
                "best_wpm": max(r.wpm for r in results),
                "average_accuracy": sum(r.accuracy for r in results) / count,
            }

        return stats_by_type

    def clear_history(self) -> bool:
        """Clear all history.

        Returns:
            True if successful
        """
        return self.history_repository.clear()
