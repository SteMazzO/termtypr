"""Domain models for ghost runs and their recordings."""

from dataclasses import dataclass
from datetime import datetime

from termtypr.core.phrase_hash import phrase_hash


@dataclass(frozen=True)
class RecordingEvent:
    """One input-state snapshot of a typing run.

    The recording captures display states rather than keystrokes: the
    Textual Input widget never delivers raw key events, and snapshots
    replay deterministically regardless of pastes or mid-cursor edits.
    """

    t: int
    """Milliseconds since the run's first keystroke."""

    w: int
    """Index of the word this input applied to."""

    v: str
    """Full input value at this moment."""

    s: bool = False
    """True when this event completed word ``w``."""


@dataclass(frozen=True)
class GhostRun:
    """A saved typing run that can be raced against."""

    phrase_text: str
    wpm: float
    accuracy: float
    duration: float
    recording: tuple[RecordingEvent, ...]
    timestamp: datetime
    id: int | None = None
    game_history_id: int | None = None

    @property
    def phrase_hash(self) -> str:
        """Stable identifier of the phrase this run was typed on."""
        return phrase_hash(self.phrase_text)

    @property
    def score(self) -> float:
        """Ranking score used for retention decisions."""
        return self.wpm * self.accuracy
