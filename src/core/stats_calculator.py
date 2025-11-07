"""Module for calculating typing test statistics"""


class StatsCalculator:
    """Class responsible for calculating typing test statistics."""

    @staticmethod
    def calculate_wpm(
        typed_words: list[str],
        target_words: list[str],
        elapsed_time_seconds: float,
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

        # Calculate uncorrected errors at character level
        uncorrected_errors = 0
        for typed, target in zip(typed_words, target_words):
            # Count character differences
            max_len = max(len(typed), len(target))
            for i in range(max_len):
                typed_char = typed[i] if i < len(typed) else ""
                target_char = target[i] if i < len(target) else ""
                if typed_char != target_char:
                    uncorrected_errors += 1

        # Calculate total characters including spaces between words
        # Most typing tests count spaces in the character total
        total_chars = sum(len(word) for word in typed_words)
        if len(typed_words) > 1:
            total_chars += len(typed_words) - 1  # Add spaces between words

        minutes = elapsed_time_seconds / 60

        # Calculate Net WPM using correct formula
        # Standard word length is 5 characters
        net_wpm = ((total_chars - uncorrected_errors) / 5) / minutes

        return round(max(net_wpm, 0), 2)

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
        # Ensure accuracy cannot be negative by capping typo_count at total_chars_typed
        effective_typos = min(typo_count, total_chars_typed)
        accuracy = ((total_chars_typed - effective_typos) / total_chars_typed) * 100

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
