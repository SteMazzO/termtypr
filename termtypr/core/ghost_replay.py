"""Deterministic playback of ghost run recordings."""

from dataclasses import dataclass
from typing import Any

from termtypr.domain.models.ghost_run import GhostRun


@dataclass(frozen=True)
class GhostReplayState:
    """The reconstructed display state of a ghost at one moment."""

    word_index: int
    current_input: str
    typed_words: list[str]
    finished: bool


class GhostReplay:
    """Replays a ghost recording as a pure function of elapsed time.

    Every query re-applies the snapshots with ``t <= elapsed_ms`` from the
    start (recordings are at most a few hundred events, so this is cheap),
    which makes playback stateless and immune to timer jitter or restarts.
    """

    def __init__(self, ghost: GhostRun):
        self.ghost = ghost
        self.target_words: list[str] = ghost.phrase_text.split()

    def state_at(self, elapsed_ms: int) -> GhostReplayState:
        """Reconstruct the ghost's display state at the given elapsed time."""
        typed_words: list[str] = []
        word_index = 0
        current_input = ""

        for event in self.ghost.recording:
            if event.t > elapsed_ms:
                break
            while len(typed_words) <= event.w:
                typed_words.append("")
            typed_words[event.w] = event.v
            if event.s:
                word_index = event.w + 1
                current_input = ""
            else:
                word_index = event.w
                current_input = event.v

        return GhostReplayState(
            word_index=word_index,
            current_input=current_input,
            typed_words=typed_words,
            finished=word_index >= len(self.target_words),
        )

    def display_data(self, elapsed_ms: int) -> dict[str, Any]:
        """Build display data in the same shape the game views consume."""
        state = self.state_at(elapsed_ms)
        return {
            "target_words": self.target_words,
            "typed_words": state.typed_words,
            "current_word_index": state.word_index,
            "current_input": state.current_input,
        }

    def time_to_reach_chars(self, char_count: int) -> int | None:
        """Milliseconds the ghost needed to have typed char_count characters.

        Progress counts completed words plus the in-progress input, the
        same metric the live stats use. Returns None when the ghost never
        typed that many characters.
        """
        if char_count <= 0:
            return 0

        completed_chars = 0
        for event in self.ghost.recording:
            if completed_chars + len(event.v) >= char_count:
                return event.t
            if event.s:
                completed_chars += len(event.v)

        return None
