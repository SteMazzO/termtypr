"""Application router.

coordinates game lifecycle, menu, history, and ghost racing.
"""

from dataclasses import replace
from typing import Any, Literal

from termtypr.application.ghost_service import GhostService
from termtypr.config import user_preferences
from termtypr.core.ghost_recorder import GhostRecorder
from termtypr.core.phrase_hash import phrase_hash
from termtypr.domain.history_repository import HistoryRepository
from termtypr.domain.models.game_result import GameResult
from termtypr.domain.models.ghost_run import GhostRun, RaceOutcome, RecordingEvent
from termtypr.games.base_game import BaseGame, GameStatus
from termtypr.games.ghost_race_game import GhostRaceGame
from termtypr.games.phrase_typing_game import PhraseTypingGame
from termtypr.games.random_words_game import RandomWordsGame

_GAME_CLASSES: list[type[BaseGame]] = [
    RandomWordsGame,
    PhraseTypingGame,
    GhostRaceGame,
]

AVAILABLE_GAMES: list[dict[str, Any]] = [
    {
        "game_class": cls,
        "name": cls.__name__,
        "display_name": cls.DISPLAY_NAME,
        "description": cls.GAME_DESCRIPTION,
    }
    for cls in _GAME_CLASSES
]


class ApplicationRouter:
    """Coordinates game lifecycle, menu navigation, and history access."""

    def __init__(
        self,
        history_repository: HistoryRepository,
        ghost_service: GhostService | None = None,
    ):
        self.history_repository = history_repository
        self.ghost_service = ghost_service
        self.ghost_recorder = GhostRecorder()
        # Ghost currently being raced; None outside of a race
        self.active_ghost: GhostRun | None = None
        # Outcome of the last finished race, for the results view
        self.last_race_outcome: RaceOutcome | None = None
        # True when the last finished run was saved as its phrase's ghost
        self.last_ghost_saved = False
        # Finished run awaiting the user's save decision (ALWAYS_ASK mode)
        self._pending_ghost_save: (
            tuple[GameResult, tuple[RecordingEvent, ...], int | None] | None
        ) = None
        self.current_game: BaseGame | None = None
        self.selected_game_index = 0

    def get_available_games(self) -> list[dict[str, Any]]:
        """Get list of available games with selection state."""
        return [
            {
                "index": idx,
                "name": game["name"],
                "display_name": game["display_name"],
                "description": game["description"],
                "is_selected": idx == self.selected_game_index,
            }
            for idx, game in enumerate(AVAILABLE_GAMES)
        ]

    def select_game(self, index: int) -> bool:
        """Select a game by index."""
        if 0 <= index < len(AVAILABLE_GAMES):
            self.selected_game_index = index
            return True
        return False

    def navigate_game_selection(self, direction: int) -> None:
        """Navigate game selection up (-1) or down (+1), wrapping around."""
        n = len(AVAILABLE_GAMES)
        self.selected_game_index = (self.selected_game_index + direction) % n

    def start_game(
        self,
        config: dict[str, Any] | None = None,
        ghost: GhostRun | None = None,
    ) -> bool:
        """Start the currently selected game.

        Args:
            config: Game-specific configuration.
            ghost: In race mode, race this ghost instead of drawing a
                random one (used by same-text restarts).
        """
        if not 0 <= self.selected_game_index < len(AVAILABLE_GAMES):
            return False

        game_def = AVAILABLE_GAMES[self.selected_game_index]
        game: BaseGame = game_def["game_class"]()

        effective_config = dict(config or {})
        if "word_count" not in effective_config:
            effective_config["word_count"] = user_preferences.word_count

        if not game.initialize(**effective_config):
            return False
        if not game.start():
            return False

        self.current_game = game
        self.ghost_recorder.reset()
        self.active_ghost = None
        self._pending_ghost_save = None
        self.last_ghost_saved = False

        if isinstance(game, GhostRaceGame) and not self._enter_ghost_race(game, ghost):
            self.current_game = None
            return False

        return True

    def _enter_ghost_race(
        self, game: GhostRaceGame, ghost: GhostRun | None = None
    ) -> bool:
        """Point a race-mode game at a saved ghost's phrase.

        Draws a random ghost when none is given.
        """
        if ghost is None and self.ghost_service is not None:
            ghost = self.ghost_service.get_random_ghost()
        if ghost is None:
            return False

        game.set_phrase(ghost.phrase_text)
        self.active_ghost = ghost
        return True

    def process_game_input(self, input_text: str, is_complete: bool = False) -> bool:
        """Process input for the active game. Returns False when no game."""
        if not self.current_game:
            return False

        game = self.current_game
        already_finished = game.is_finished()
        word_index_before = game.current_word_index

        result = game.process_input(input_text, is_complete)

        # Record phrase runs as input snapshots for ghost racing. Recording
        # happens after processing so the run clock (start_time) exists.
        elapsed = game.elapsed_seconds()
        if (
            not already_finished
            and game.phrase_text is not None
            and elapsed is not None
        ):
            self.ghost_recorder.record(
                elapsed_ms=int(elapsed * 1000),
                word_index=word_index_before,
                value=input_text,
                completed_word=game.current_word_index > word_index_before,
            )

        return result.get("status") != "error"

    def finish_game(self) -> GameResult | None:
        """Finish the current game, persist the result, and return it."""
        if not self.current_game:
            return None
        if self.current_game.status is GameStatus.CANCELLED:
            return None

        result = self.current_game.finish()

        best = self.history_repository.get_best()
        result = replace(
            result,
            is_new_record=result.wpm > 0 and (best is None or result.wpm > best.wpm),
            previous_best=best.wpm if best else None,
        )

        history_id = self.history_repository.save(result)

        # A race ends with this run; keep the outcome for the results view
        self.last_race_outcome = None
        if self.active_ghost is not None:
            self.last_race_outcome = RaceOutcome(
                ghost=self.active_ghost, player_duration=result.duration
            )
            self.active_ghost = None

        if self.ghost_service is not None:
            if self.ghost_service.should_auto_save(result):
                self.ghost_service.save_ghost(
                    result, self.ghost_recorder.recording, history_id
                )
                self.last_ghost_saved = True
            elif self.ghost_service.should_prompt(result):
                self._pending_ghost_save = (
                    result,
                    self.ghost_recorder.recording,
                    history_id,
                )

        return result

    def has_pending_ghost_save(self) -> bool:
        """Check whether a finished run awaits a ghost-save decision."""
        return self._pending_ghost_save is not None

    def save_pending_ghost(self) -> bool:
        """Save the run awaiting a decision (ALWAYS_ASK mode).

        Returns:
            True when a pending run was saved.
        """
        if self._pending_ghost_save is None or self.ghost_service is None:
            return False

        result, recording, history_id = self._pending_ghost_save
        self.ghost_service.save_ghost(result, recording, history_id)
        self._pending_ghost_save = None
        self.last_ghost_saved = True
        return True

    def has_ghost_for_current_phrase(self) -> bool:
        """Check whether the current game's phrase has a saved ghost."""
        if self.ghost_service is None or self.current_game is None:
            return False
        phrase_text = self.current_game.phrase_text
        if phrase_text is None:
            return False
        return self.ghost_service.has_ghost_for_phrase(phrase_hash(phrase_text))

    def start_ghost_rematch(self) -> bool:
        """Restart the finished phrase as a race against its saved ghost.

        Returns:
            True when a race started; False when there is no game, no
            phrase, or no saved ghost for it.
        """
        if self.ghost_service is None or self.current_game is None:
            return False
        phrase_text = self.current_game.phrase_text
        if phrase_text is None:
            return False

        ghost = self.ghost_service.get_ghost_for_phrase(phrase_hash(phrase_text))
        if ghost is None:
            return False

        if not self.restart_game(keep_same_text=True):
            return False

        self.active_ghost = ghost
        return True

    def cancel_game(self) -> bool:
        """Cancel the current game without saving results."""
        if not self.current_game:
            return False
        self.current_game.cancel()
        self.current_game = None
        self.active_ghost = None
        return True

    def restart_game(self, keep_same_text: bool = False) -> bool:
        """Restart the current game without resetting menu selection.

        Args:
            keep_same_text: If True, reuse the same target words/phrases.

        Returns:
            True if the game was successfully restarted.
        """
        saved_words = None
        saved_phrase = None
        # A restart on the same text keeps the race going; new text ends it
        saved_ghost = self.active_ghost if keep_same_text else None
        if keep_same_text and self.current_game:
            saved_words = self.current_game.target_words.copy()
            saved_phrase = self.current_game.phrase_text

        # Clean up the current game without touching selection
        if self.current_game:
            if not self.current_game.is_finished():
                self.current_game.cancel()
            self.current_game = None

        # Passing the saved ghost means a same-text race restart reuses it
        # instead of drawing (and possibly failing to find) a random one
        if not self.start_game(ghost=saved_ghost):
            return False

        if saved_words and self.current_game:
            self.current_game.target_words = saved_words
            self.current_game.phrase_text = saved_phrase
        if keep_same_text:
            # New text keeps whatever start_game decided (nothing for
            # normal games, a fresh random ghost in race mode)
            self.active_ghost = saved_ghost

        return True

    def is_game_active(self) -> bool:
        """Check if a game is currently active (ready or in-progress)."""
        return self.current_game is not None and not self.current_game.is_finished()

    def is_game_finished(self) -> bool:
        """Check if the current game has completed."""
        return self.current_game is not None and self.current_game.is_finished()

    def get_game_display_data(self) -> dict[str, Any] | None:
        """Get display data for the active game."""
        if not self.current_game:
            return None
        return self.current_game.get_display_data()

    def get_game_stats(self) -> dict[str, Any] | None:
        """Get current game statistics."""
        if not self.current_game:
            return None
        return self.current_game.get_current_stats()

    def return_to_main_menu(self) -> None:
        """Return to main menu, cleaning up any active game."""
        if self.current_game:
            if not self.current_game.is_finished():
                self.current_game.cancel()
            self.current_game = None
        self.active_ghost = None

    def get_all_games(self, sort: Literal["asc", "desc"] = "desc") -> list[GameResult]:
        """Get all game results from history."""
        return self.history_repository.get_all(sort=sort)
