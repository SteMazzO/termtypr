"""Typing test statistics calculations."""

# Results measured over less than this are not meaningful (and would produce
# absurd WPM values from near-zero elapsed times).
MIN_ELAPSED_SECONDS = 1.0

_CHARS_PER_WORD = 5


def _total_chars(typed_words: list[str]) -> int:
    """Count typed characters, including one space between consecutive words."""
    total = sum(len(word) for word in typed_words)
    if len(typed_words) > 1:
        total += len(typed_words) - 1
    return total


def count_uncorrected_errors(typed_words: list[str], target_words: list[str]) -> int:
    """Count character positions where the submitted words differ from the target.

    Missing and extra characters each count as one error.
    """
    errors = 0
    for typed, target in zip(typed_words, target_words, strict=False):
        max_len = max(len(typed), len(target))
        for i in range(max_len):
            typed_char = typed[i] if i < len(typed) else ""
            target_char = target[i] if i < len(target) else ""
            if typed_char != target_char:
                errors += 1
    return errors


def calculate_wpm(
    typed_words: list[str],
    target_words: list[str],
    elapsed_time_seconds: float,
) -> float:
    """Calculate net words per minute (WPM).

    Uses the standard formula: ((total_chars - uncorrected_errors) / 5) / minutes
    """
    if elapsed_time_seconds < MIN_ELAPSED_SECONDS:
        return 0.0

    uncorrected_errors = count_uncorrected_errors(typed_words, target_words)
    minutes = elapsed_time_seconds / 60
    net_chars = _total_chars(typed_words) - uncorrected_errors
    net_wpm = (net_chars / _CHARS_PER_WORD) / minutes

    return round(max(net_wpm, 0), 2)


def calculate_raw_wpm(typed_words: list[str], elapsed_time_seconds: float) -> float:
    """Calculate raw (gross) WPM: all typed characters, errors included."""
    if elapsed_time_seconds < MIN_ELAPSED_SECONDS:
        return 0.0

    minutes = elapsed_time_seconds / 60
    raw_wpm = (_total_chars(typed_words) / _CHARS_PER_WORD) / minutes
    return round(max(raw_wpm, 0), 2)


def calculate_accuracy(total_keystrokes: int, error_keystrokes: int) -> float:
    """Calculate keystroke accuracy as a percentage.

    Accuracy is correct keystrokes over total keystrokes, so mistakes count
    even when later corrected.
    """
    if total_keystrokes <= 0:
        return 100.0

    correct = max(total_keystrokes - error_keystrokes, 0)
    return round((correct / total_keystrokes) * 100, 2)
