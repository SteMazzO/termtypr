"""Application router for coordinating navigation and business logic."""

from enum import Enum
from typing import Any, Optional

from src.application.controllers.game_controller import GameController
from src.application.services.stats_service import StatsService
from src.domain.models.game_result import GameResult
from src.domain.repositories.history_repository import HistoryRepository
from src.games.base_game import BaseGame
from src.games.phrase_typing_game import PhraseTypingGame
from src.games.random_words_game import RandomWordsGame


class AppScreen(Enum):
    """Application screens/views."""

    MAIN_MENU = "main_menu"
    GAME_SELECTION = "game_selection"
    GAME_CONFIG = "game_config"
    GAME_ACTIVE = "game_active"
    GAME_RESULTS = "game_results"
    STATISTICS = "statistics"
    SETTINGS = "settings"


class GameDefinition:
    """Defines an available game type."""

    def __init__(
        self,
        game_class: type[BaseGame],
        name: str,
        display_name: str,
        description: str,
    ):
        """Initialize game definition.

        Args:
            game_class: The game class to instantiate
            name: Internal identifier for the game
            display_name: Human-readable name for display
            description: Description of the game mode
        """
        self.game_class = game_class
        self.name = name
        self.display_name = display_name
        self.description = description

    def create_instance(self) -> BaseGame:
        """Create a new instance of this game type.

        Returns:
            New game instance
        """
        return self.game_class()


class ApplicationRouter:
    """Coordinates application navigation and business logic.

    This router acts as the central coordinator between:
    - Controllers (game lifecycle management)
    - Services (statistics, data access)
    - Views (UI presentation)

    It manages the application state machine and delegates to appropriate
    components based on the current screen and user actions.
    """

    def __init__(self, history_repository: HistoryRepository):
        """Initialize the application router.

        Args:
            history_repository: Repository for game history persistence
        """
        self.history_repository = history_repository
        self.stats_service = StatsService(history_repository)
        self.game_controller: Optional[GameController] = None

        # Current application state
        self.current_screen = AppScreen.MAIN_MENU
        self.selected_game_index = 0

        # Define available games
        self.available_games: list[GameDefinition] = [
            GameDefinition(
                game_class=RandomWordsGame,
                name="random_words",
                display_name="Random Words",
                description="Type randomly selected words as fast and accurately as possible",
            ),
            GameDefinition(
                game_class=PhraseTypingGame,
                name="phrase_typing",
                display_name="Phrase Typing",
                description="Type complete phrases and quotes to improve your typing flow",
            ),
        ]

    # ==================== Navigation Methods ====================

    def navigate_to_screen(self, screen: AppScreen) -> bool:
        """Navigate to a specific screen.

        Args:
            screen: Target screen to navigate to

        Returns:
            True if navigation was successful
        """
        # Validate navigation based on current state
        if screen == AppScreen.GAME_ACTIVE and not self.game_controller:
            return False

        old_screen = self.current_screen
        self.current_screen = screen

        # Clean up when leaving certain screens
        if old_screen == AppScreen.GAME_ACTIVE and screen != AppScreen.GAME_ACTIVE:
            # Keep controller for results screen, but clean up for others
            if screen != AppScreen.GAME_RESULTS and self.game_controller:
                self._cleanup_game_controller()

        return True

    def return_to_main_menu(self) -> None:
        """Return to main menu, cleaning up any active game."""
        if self.game_controller:
            if self.game_controller.is_game_active():
                self.game_controller.cancel_game()
            self._cleanup_game_controller()

        self.current_screen = AppScreen.MAIN_MENU
        self.selected_game_index = 0

    def get_current_screen(self) -> AppScreen:
        """Get the current screen.

        Returns:
            Current application screen
        """
        return self.current_screen

    # ==================== Game Selection Methods ====================

    def get_available_games(self) -> list[dict[str, Any]]:
        """Get list of available games with metadata.

        Returns:
            List of game definitions with display information
        """
        return [
            {
                "index": idx,
                "name": game.name,
                "display_name": game.display_name,
                "description": game.description,
                "is_selected": idx == self.selected_game_index,
            }
            for idx, game in enumerate(self.available_games)
        ]

    def select_game(self, index: int) -> bool:
        """Select a game by index.

        Args:
            index: Index of the game to select

        Returns:
            True if selection was valid
        """
        if 0 <= index < len(self.available_games):
            self.selected_game_index = index
            return True
        return False

    def navigate_game_selection(self, direction: int) -> bool:
        """Navigate game selection up or down.

        Args:
            direction: -1 for up, 1 for down

        Returns:
            True if navigation was successful
        """
        new_index = self.selected_game_index + direction

        # Wrap around
        if new_index < 0:
            new_index = len(self.available_games) - 1
        elif new_index >= len(self.available_games):
            new_index = 0

        self.selected_game_index = new_index
        return True

    def get_selected_game_definition(self) -> Optional[GameDefinition]:
        """Get the currently selected game definition.

        Returns:
            Selected game definition or None if invalid
        """
        if 0 <= self.selected_game_index < len(self.available_games):
            return self.available_games[self.selected_game_index]
        return None

    # ==================== Game Lifecycle Methods ====================

    def start_game(self, config: Optional[dict[str, Any]] = None) -> bool:
        """Start the currently selected game.

        Args:
            config: Optional game configuration (word_count, etc.)

        Returns:
            True if game started successfully
        """
        # Get selected game definition
        game_def = self.get_selected_game_definition()
        if not game_def:
            return False

        # Create game instance
        game_instance = game_def.create_instance()

        # Initialize game controller if needed
        if not self.game_controller:
            self.game_controller = GameController(
                history_repository=self.history_repository
            )

        # Start the game with config
        success = self.game_controller.start_game(game_instance, config or {})

        if success:
            self.current_screen = AppScreen.GAME_ACTIVE
            return True

        # Cleanup on failure
        self._cleanup_game_controller()
        return False

    def process_game_input(self, input_text: str, is_complete: bool = False) -> bool:
        """Process input for active game.

        Args:
            input_text: Text input from user
            is_complete: Whether this is a complete word submission

        Returns:
            True if input was processed successfully
        """
        if not self.game_controller:
            return False

        result = self.game_controller.process_input(input_text, is_complete)

        # Check if game finished
        if self.game_controller.is_game_finished():
            self.current_screen = AppScreen.GAME_RESULTS

        return result.get("status") != "error"

    def finish_game(self) -> Optional[GameResult]:
        """Finish the current game and get results.

        Returns:
            GameResult if game was active, None otherwise
        """
        if not self.game_controller:
            return None

        result = self.game_controller.finish_game()

        if result:
            self.current_screen = AppScreen.GAME_RESULTS

        return result

    def cancel_game(self) -> bool:
        """Cancel the current game without saving.

        Returns:
            True if game was cancelled
        """
        if not self.game_controller:
            return False

        self.game_controller.cancel_game()
        self._cleanup_game_controller()
        self.current_screen = AppScreen.MAIN_MENU

        return True

    def is_game_active(self) -> bool:
        """Check if a game is currently active.

        Returns:
            True if game is active (started and not finished)
        """
        return (
            self.game_controller is not None
            and self.game_controller.current_game is not None
            and self.game_controller.game_state is not None
            and not self.game_controller.is_game_finished()
        )

    def get_game_display_data(self) -> Optional[dict[str, Any]]:
        """Get display data for active game.

        Returns:
            Display data dictionary or None if no active game
        """
        if not self.game_controller:
            return None

        return self.game_controller.get_display_data()

    def get_game_stats(self) -> Optional[dict[str, Any]]:
        """Get current game statistics.

        Returns:
            Statistics dictionary or None if no active game
        """
        if not self.game_controller:
            return None

        return self.game_controller.get_current_stats()

    # ==================== Statistics Methods ====================

    def get_statistics_summary(self) -> dict[str, Any]:
        """Get comprehensive statistics summary.

        Returns:
            Statistics summary including progress, records, etc.
        """
        return {
            "progress": self.stats_service.get_progress_summary(),
            "best_performance": self.stats_service.get_best_performance(),
            "recent_games": self.stats_service.get_recent_results(limit=10),
            "game_type_stats": self.stats_service.get_game_type_stats(),
        }

    def get_recent_games(self, limit: int = 10, sort: str = "desc") -> list[GameResult]:
        """Get recent game results.

        Args:
            limit: Maximum number of results to return
            sort: Sort order - 'desc' for newest first (default), 'asc' for oldest first

        Returns:
            List of recent game results
        """
        return self.stats_service.get_recent_results(limit, sort=sort)

    def get_all_games(self, sort: str = "desc") -> list[GameResult]:
        """Get all game results from history.

        Args:
            sort: Sort order - 'desc' for newest first (default), 'asc' for oldest first

        Returns:
            List of all game results
        """
        return self.stats_service.get_all_results(sort=sort)

    def get_formatted_stats_table(self, limit: int = 10) -> list[dict[str, Any]]:
        """Get formatted statistics table data.

        Args:
            limit: Number of entries to include

        Returns:
            List of formatted table rows
        """
        return self.stats_service.format_stats_table(limit)

    def clear_history(self) -> bool:
        """Clear all game history.

        Returns:
            True if history was cleared successfully
        """
        return self.stats_service.clear_history()

    # ==================== Private Helper Methods ====================

    def _cleanup_game_controller(self) -> None:
        """Clean up the game controller."""
        if self.game_controller:
            # Cancel if still active
            if self.game_controller.is_game_active():
                self.game_controller.cancel_game()
            self.game_controller = None
