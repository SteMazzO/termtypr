"""Ghost save conditions and persistence coordination."""

from dataclasses import replace

from termtypr.config import user_preferences
from termtypr.domain.ghost_repository import GhostRepository
from termtypr.domain.models.game_result import GameResult
from termtypr.domain.models.ghost_run import GhostRun, RecordingEvent
from termtypr.domain.models.user_preferences import GhostSaveMode


class GhostService:
    """Decides when a run becomes a ghost and applies retention rules."""

    def __init__(self, repository: GhostRepository):
        self.repository = repository

    def get_ghost_for_phrase(self, phrase_hash: str) -> GhostRun | None:
        """Get the saved ghost for a phrase, if any."""
        return self.repository.get_by_phrase_hash(phrase_hash)

    def get_random_ghost(self) -> GhostRun | None:
        """Get a random saved ghost, or None when there are none."""
        return self.repository.get_random()

    def qualifies(self, result: GameResult) -> bool:
        """Check the quality floor every ghost save must meet.

        A run qualifies when it is a phrase run with a meaningful WPM and
        at least the configured minimum accuracy - a fast but sloppy run
        makes a poor opponent.
        """
        return (
            result.phrase_text is not None
            and result.wpm > 0
            and result.accuracy >= user_preferences.ghost_min_accuracy
        )

    def should_prompt(self, result: GameResult) -> bool:
        """Check whether to ask the user about saving this run (ASK mode)."""
        return (
            user_preferences.ghost_save_mode is GhostSaveMode.ALWAYS_ASK
            and self.qualifies(result)
        )

    def should_auto_save(self, result: GameResult) -> bool:
        """Check whether this run is saved as a ghost without asking.

        In both automatic modes a run only replaces the phrase's existing
        ghost when it scores higher - each phrase keeps its best run.
        """
        mode = user_preferences.ghost_save_mode
        if mode not in (GhostSaveMode.AUTO_BEST, GhostSaveMode.AUTO_THRESHOLD):
            return False
        if not self.qualifies(result):
            return False
        if (
            mode is GhostSaveMode.AUTO_THRESHOLD
            and result.wpm < user_preferences.ghost_wpm_threshold
        ):
            return False

        existing = self.repository.get_by_phrase_hash(result.phrase_hash)
        return existing is None or result.wpm * result.accuracy > existing.score

    def save_ghost(
        self,
        result: GameResult,
        recording: tuple[RecordingEvent, ...],
        history_id: int | None = None,
    ) -> GhostRun:
        """Persist a run as the ghost for its phrase and enforce the cap."""
        if result.phrase_text is None:
            raise ValueError("Only phrase runs can be saved as ghosts")

        ghost = GhostRun(
            phrase_text=result.phrase_text,
            wpm=result.wpm,
            accuracy=result.accuracy,
            duration=result.duration,
            recording=recording,
            timestamp=result.timestamp,
            game_history_id=history_id,
        )
        ghost_id = self.repository.save(ghost)
        self.repository.prune(user_preferences.max_ghosts_total)
        return replace(ghost, id=ghost_id)
