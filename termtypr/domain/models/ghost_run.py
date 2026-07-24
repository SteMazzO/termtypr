"""Domain models for ghost runs and their recordings."""

from dataclasses import dataclass
from datetime import datetime

from termtypr.core.phrase_hash import phrase_hash


def ghost_score(wpm: float, accuracy: float) -> float:
    """Ranking score used for all ghost retention decisions.

    The single definition: repositories and services must call this
    instead of re-deriving the formula.
    """
    return wpm * accuracy


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
        return ghost_score(self.wpm, self.accuracy)


@dataclass(frozen=True)
class RaceOutcome:
    """The result of a finished race against a ghost."""

    ghost: GhostRun
    player_duration: float

    @property
    def won(self) -> bool:
        """True when the player finished before the ghost."""
        return self.player_duration < self.ghost.duration

    @property
    def delta_seconds(self) -> float:
        """Seconds the player finished behind (positive) or ahead of the ghost."""
        return self.player_duration - self.ghost.duration
