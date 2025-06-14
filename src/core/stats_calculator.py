"""Module for calculating typing test statistics"""


class StatsCalculator:
    """Class responsible for calculating typing test statistics."""

    @staticmethod
    def calculate_wpm(
        typed_words: list[str], target_words: list[str], elapsed_time_seconds: float
    ) -> float:
        """Calculate words per minute (WPM).

        Args:
            typed_words: List of words typed by the user.
            target_words: List of target words that should have been typed.
            elapsed_time_seconds: Time taken to complete the test in seconds.

        Returns:
            Words per minute.
        """
        # Check elapsed time is not zero
        if not elapsed_time_seconds:
            return 0.0

        # Standard calculation: (characters typed / 5) / minutes
        # We use 5 characters as an average word length standard

        # Ensure last word is not counted if it is incomplete
        if typed_words and typed_words[-1] != target_words[len(typed_words) - 1]:
            typed_words = typed_words[:-1]

        # Only count correctly typed words
        correct_words = [
            typed for typed, target in zip(typed_words, target_words) if typed == target
        ]

        if not correct_words or not elapsed_time_seconds:
            return 0.0

        total_chars = sum(len(word) for word in correct_words)
        minutes = elapsed_time_seconds / 60

        wpm = (total_chars / 5) / minutes
        return round(wpm, 2)

    @staticmethod
    def calculate_accuracy(
        typed_words: list[str], target_words: list[str], typo_count: int
    ) -> float:
        """Calculate typing accuracy.

        Args:
            typed_words: List of words typed by the user.
            target_words: List of target words that should have been typed.
            typo_count: Number of typos made during the test.

        Returns:
            Accuracy as a percentage.
        """
        if not typed_words or not target_words:
            return 0.0

        typed_text = "".join(typed_words)

        # Calculate total characters typed including corrections
        total_chars_typed = len(typed_text)

        if total_chars_typed == 0:
            return 0.0

        # Calculate accuracy considering typos
        accuracy = ((total_chars_typed - typo_count) / total_chars_typed) * 100

        return round(accuracy, 2)

    @staticmethod
    def get_statistics(
        typed_words: list[str],
        target_words: list[str],
        elapsed_time_seconds: float,
        typo_count: int,
    ) -> dict:
        """Get comprehensive typing test statistics.

        Args:
            typed_words: List of words typed by the user.
            target_words: List of target words that should have been typed.
            elapsed_time_seconds: Time taken to complete the test in seconds.
            typo_count: Number of typos made during the test.

        Returns:
            Dictionary of statistics.
        """
        wpm = StatsCalculator.calculate_wpm(
            typed_words, target_words, elapsed_time_seconds
        )
        accuracy = StatsCalculator.calculate_accuracy(
            typed_words, target_words, typo_count
        )

        return {
            "wpm": wpm,
            "accuracy": accuracy,
            "duration": round(elapsed_time_seconds, 2),
            "typed_word_count": len(typed_words),
            "target_word_count": len(target_words),
            "is_completed": len(typed_words) >= len(target_words),
        }
