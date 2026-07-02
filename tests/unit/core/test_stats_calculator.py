"""Tests for typing statistics calculations."""

from termtypr.core.stats_calculator import (
    calculate_accuracy,
    calculate_raw_wpm,
    calculate_wpm,
    count_uncorrected_errors,
)


class TestCountUncorrectedErrors:
    """Tests for character-level error counting."""

    def test_no_errors(self):
        """Identical words produce zero errors."""
        assert count_uncorrected_errors(["hello", "world"], ["hello", "world"]) == 0

    def test_single_wrong_char(self):
        """One mismatched character counts as one error."""
        assert count_uncorrected_errors(["hxllo"], ["hello"]) == 1

    def test_missing_chars_count(self):
        """Each missing character counts as one error."""
        assert count_uncorrected_errors(["cat"], ["catalog"]) == 4

    def test_extra_chars_count(self):
        """Each extra typed character counts as one error."""
        assert count_uncorrected_errors(["catss"], ["cat"]) == 2


class TestCalculateWpm:
    """Tests for net WPM calculation."""

    def test_perfect_typing(self):
        """11 chars (incl. space) in 60s -> 2.2 WPM."""
        assert calculate_wpm(["hello", "world"], ["hello", "world"], 60.0) == 2.2

    def test_errors_reduce_wpm(self):
        """Each uncorrected error removes one character of credit."""
        assert calculate_wpm(["hxllo", "world"], ["hello", "world"], 60.0) == 2.0

    def test_never_negative(self):
        """WPM is clamped at zero when errors exceed typed characters."""
        assert calculate_wpm(["", ""], ["hello", "world"], 60.0) == 0.0

    def test_below_minimum_elapsed_returns_zero(self):
        """Sub-second measurements are meaningless and return 0."""
        assert calculate_wpm(["hello"], ["hello"], 0.5) == 0.0

    def test_zero_elapsed_returns_zero(self):
        """Zero elapsed time does not divide by zero."""
        assert calculate_wpm(["hello"], ["hello"], 0.0) == 0.0


class TestCalculateRawWpm:
    """Tests for raw (gross) WPM calculation."""

    def test_ignores_errors(self):
        """Raw WPM counts all typed characters, right or wrong."""
        assert calculate_raw_wpm(["hxllo", "world"], 60.0) == 2.2

    def test_below_minimum_elapsed_returns_zero(self):
        """Sub-second measurements return 0."""
        assert calculate_raw_wpm(["hello"], 0.5) == 0.0


class TestCalculateAccuracy:
    """Tests for keystroke accuracy calculation."""

    def test_no_keystrokes_is_perfect(self):
        """No keystrokes yet means 100% accuracy."""
        assert calculate_accuracy(0, 0) == 100.0

    def test_all_correct(self):
        """No errors means 100% accuracy."""
        assert calculate_accuracy(50, 0) == 100.0

    def test_partial_errors(self):
        """2 errors out of 10 keystrokes -> 80%."""
        assert calculate_accuracy(10, 2) == 80.0

    def test_errors_exceeding_keystrokes_clamp_to_zero(self):
        """Accuracy never goes negative."""
        assert calculate_accuracy(5, 10) == 0.0
