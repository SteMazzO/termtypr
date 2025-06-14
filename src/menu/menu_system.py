"""Menu system for the typing trainer application."""

from enum import Enum

from src.games.base_game import BaseGame
from src.games.phrase_typing_game import PhraseTypingGame
from src.games.random_words_game import RandomWordsGame


class MenuState(Enum):
    """State of the menu system."""

    MAIN_MENU = "main_menu"
    GAME_CONFIG = "game_config"
    IN_GAME = "in_game"
    GAME_RESULTS = "game_results"


class GameMenuItem:
    """Represents a game option in the menu."""

    def __init__(
        self,
        game_class: type[BaseGame],
        display_name: str,
        description: str
    ):
        self.game_class = game_class
        self.display_name = display_name
        self.description = description

    def create_game_instance(self) -> BaseGame:
        """Create a new instance of this game."""
        return self.game_class()


class MenuSystem:
    """Manages the main menu and navigation between games."""

    def __init__(self):
        self.state = MenuState.MAIN_MENU
        self.current_game: BaseGame | None = None
        self.selected_menu_index = 0        # Register available games
        self.game_menu_items: list[GameMenuItem] = [
            GameMenuItem(
                RandomWordsGame,
                "Random Words",
                "Type randomly selected words as fast and accurately as possible"
            ),
            GameMenuItem(
                PhraseTypingGame,
                "Phrase Typing",
                "Type complete phrases and quotes to improve your typing flow"
            ),
        ]

    def get_main_menu_data(self) -> dict[str, any]:
        """Get data for displaying the main menu."""
        return {
            "title": "TermTypr - Typing Practice Games",
            "subtitle": "Choose a typing practice mode:",
            "games": [
                {
                    "index": i,
                    "display_name": item.display_name,
                    "description": item.description,
                    "is_selected": i == self.selected_menu_index,
                }
                for i, item in enumerate(self.game_menu_items)
            ],
            "selected_index": self.selected_menu_index,
            "instructions": [
                "Use ↑/↓ arrow keys or numbers to navigate",
                "Press ENTER to select a game",
                "Press 'Ctrl+Q' to quit",
                "Press 'Ctrl+S' to view statistics",
            ],
        }

    def navigate_menu(self, direction: int) -> bool:
        """Navigate the menu selection.

        Args:
            direction: -1 for up, 1 for down

        Returns:
            True if navigation was successful
        """
        if self.state != MenuState.MAIN_MENU:
            return False

        new_index = self.selected_menu_index + direction

        # Wrap around
        if new_index < 0:
            new_index = len(self.game_menu_items) - 1
        elif new_index >= len(self.game_menu_items):
            new_index = 0

        self.selected_menu_index = new_index
        return True

    def select_game_by_index(self, index: int) -> bool:
        """Select a game by its menu index.

        Args:
            index: Index of the game to select

        Returns:
            True if selection was successful
        """
        if self.state != MenuState.MAIN_MENU:
            return False

        if 0 <= index < len(self.game_menu_items):
            self.selected_menu_index = index
            return True

        return False

    def start_selected_game(self, config: dict[str, any] = None) -> bool:
        """Start the currently selected game with given configuration.

        Args:
            config: Configuration dictionary for the game

        Returns:
            True if game started successfully
        """
        if self.state != MenuState.MAIN_MENU:
            return False

        if 0 <= self.selected_menu_index < len(self.game_menu_items):
            item = self.game_menu_items[self.selected_menu_index]
            self.current_game = item.create_game_instance()

            # Initialize game with config
            config = config or {}
            if not self.current_game.initialize(**config):
                self.current_game = None
                return False

            # Start the game
            if self.current_game.start():
                self.state = MenuState.IN_GAME
                return True
            self.current_game = None
            return False

        return False

    def get_current_game(self) -> BaseGame | None:
        """Get the currently active game instance."""
        return self.current_game

    def finish_current_game(self) -> dict[str, any] | None:
        """Finish the current game and get results.

        Returns:
            Game results dictionary or None if no active game
        """
        if self.current_game and self.state == MenuState.IN_GAME:
            result = self.current_game.finish()
            self.state = MenuState.GAME_RESULTS
            return result.to_dict()

        return None

    def return_to_main_menu(self) -> None:
        """Return to the main menu."""
        if self.current_game:
            if self.current_game.is_active():
                self.current_game.cancel()
            self.current_game = None

        self.state = MenuState.MAIN_MENU
        self.selected_menu_index = 0

    def get_current_state(self) -> MenuState:
        """Get the current menu state."""
        return self.state

    def is_in_game(self) -> bool:
        """Check if currently in a game."""
        return self.state == MenuState.IN_GAME and self.current_game is not None

    def get_available_games_info(self) -> list[dict[str, str]]:
        """Get information about all available games.

        Returns:
            List of dictionaries with game information
        """
        return [
            {
                "name": item.display_name,
                "description": item.description,
                "class_name": item.game_class.__name__,
            }
            for item in self.game_menu_items
        ]
