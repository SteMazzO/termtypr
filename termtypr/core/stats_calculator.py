"""Typing test statistics calculations."""


def calculate_wpm(
    typed_words: list[str],
    target_words: list[str],
    elapsed_time_seconds: float,
) -> float:
    """Calculate net words per minute (WPM).

    Uses the standard formula: ((total_chars - uncorrected_errors) / 5) / minutes
    """
    if not elapsed_time_seconds:
        return 0.0

    uncorrected_errors = 0
    for typed, target in zip(typed_words, target_words, strict=False):
        max_len = max(len(typed), len(target))
        for i in range(max_len):
            typed_char = typed[i] if i < len(typed) else ""
            target_char = target[i] if i < len(target) else ""
            if typed_char != target_char:
                uncorrected_errors += 1

    total_chars = sum(len(word) for word in typed_words)
    if len(typed_words) > 1:
        total_chars += len(typed_words) - 1  # spaces between words

    minutes = elapsed_time_seconds / 60
    net_wpm = ((total_chars - uncorrected_errors) / 5) / minutes

    return round(max(net_wpm, 0), 2)


def calculate_accuracy(
    typed_words: list[str], target_words: list[str], typo_count: int
) -> float:
    """Calculate typing accuracy as a percentage."""
    if not typed_words or not target_words:
        return 0.0

    total_chars_typed = sum(len(w) for w in typed_words)
    if total_chars_typed == 0:
        return 0.0

    effective_typos = min(typo_count, total_chars_typed)
    accuracy = ((total_chars_typed - effective_typos) / total_chars_typed) * 100
    return round(accuracy, 2)
