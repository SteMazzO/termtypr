"""Application router.

coordinates game lifecycle, menu, and history.
"""

from dataclasses import replace
from typing import Any, Literal

from termtypr.config import user_preferences
from termtypr.domain.history_repository import HistoryRepository
from termtypr.domain.models.game_result import GameResult
from termtypr.games.base_game import BaseGame
from termtypr.games.phrase_typing_game import PhraseTypingGame
from termtypr.games.random_words_game import RandomWordsGame

_GAME_CLASSES: list[type[BaseGame]] = [RandomWordsGame, PhraseTypingGame]

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

    def __init__(self, history_repository: HistoryRepository):
        self.history_repository = history_repository
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

    def start_game(self, config: dict[str, Any] | None = None) -> bool:
        """Start the currently selected game."""
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
        return True

    def process_game_input(self, input_text: str, is_complete: bool = False) -> bool:
        """Process input for the active game. Returns False when no game."""
        if not self.current_game:
            return False
        result = self.current_game.process_input(input_text, is_complete)
        return result.get("status") != "error"

    def finish_game(self) -> GameResult | None:
        """Finish the current game, persist the result, and return it."""
        if not self.current_game:
            return None

        result = self.current_game.finish()

        best = self.history_repository.get_best()
        result = replace(
            result,
            is_new_record=result.wpm > 0 and (best is None or result.wpm > best.wpm),
            previous_best=best.wpm if best else None,
        )

        self.history_repository.save(result)
        return result

    def cancel_game(self) -> bool:
        """Cancel the current game without saving results."""
        if not self.current_game:
            return False
        self.current_game.cancel()
        self.current_game = None
        return True

    def restart_game(self, keep_same_text: bool = False) -> bool:
        """Restart the current game without resetting menu selection.

        Args:
            keep_same_text: If True, reuse the same target words/phrases.

        Returns:
            True if the game was successfully restarted.
        """
        saved_words = None
        if keep_same_text and self.current_game:
            saved_words = self.current_game.target_words.copy()

        # Clean up the current game without touching selection
        if self.current_game:
            if not self.current_game.is_finished():
                self.current_game.cancel()
            self.current_game = None

        if not self.start_game():
            return False

        if saved_words and self.current_game:
            self.current_game.target_words = saved_words

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
        self.selected_game_index = 0

    def get_all_games(self, sort: Literal["asc", "desc"] = "desc") -> list[GameResult]:
        """Get all game results from history."""
        return self.history_repository.get_all(sort=sort)
