"""Capture of input-state snapshots during a typing run."""

from termtypr.domain.models.ghost_run import RecordingEvent


class GhostRecorder:
    """Accumulates the input snapshots of one typing run."""

    def __init__(self):
        self._events: list[RecordingEvent] = []

    @property
    def recording(self) -> tuple[RecordingEvent, ...]:
        """The events captured so far."""
        return tuple(self._events)

    def reset(self) -> None:
        """Drop all captured events (a new run is starting)."""
        self._events.clear()

    def record(
        self, elapsed_ms: int, word_index: int, value: str, completed_word: bool
    ) -> None:
        """Capture one input snapshot.

        Args:
            elapsed_ms: Milliseconds since the run's first keystroke.
            word_index: Index of the word the input applied to.
            value: Full input value at this moment.
            completed_word: True when this input completed the word.
        """
        self._events.append(
            RecordingEvent(t=elapsed_ms, w=word_index, v=value, s=completed_word)
        )
