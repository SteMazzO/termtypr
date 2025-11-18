"""TermTypr Application"""

from typing import Optional

from textual.app import App, ComposeResult
from textual.containers import Container
from textual.widgets import Footer, Header, Input

from src.application.router.application_router import ApplicationRouter
from src.config import THEMES
from src.domain.models.game_result import GameResult
from src.domain.models.game_state import GameState
from src.infrastructure.persistence.json_history_repository import JsonHistoryRepository
from src.ui.game_view import GameView
from src.ui.main_menu_view import MainMenuView
from src.ui.results_view import ResultsView
from src.ui.stats_view import StatsView


class TermTypr(App):
    """Main application class."""

    CSS = """
    Screen {
        background: $background;
    }
    
    #main-container {
        height: 1fr;
        margin: 0 1;
    }
    
    #input-container {
        height: 3;
        margin: 0 1 1 1;
    }
    
    Input {
        margin: 0 1;
    }
    
    #game-words-view {
        width: 70%;
        margin: 0 1 0 0;
    }
    
    #game-stats-view {
        width: 30%;
        min-width: 25;
        margin: 0 0 0 1;
    }
    """

    BINDINGS = [
        ("ctrl+q", "quit", "Quit"),
        ("escape", "escape_action", "Restart/Menu"),
    ]

    def __init__(self, theme_name: str = "default"):
        """Initialize the application."""
        super().__init__()
        self.theme_name = theme_name
        self.theme_colors = THEMES.get(theme_name, THEMES["default"])

        # Set CSS variables for theme colors
        self.background = self.theme_colors["background"]

        # Initialize application router with repository
        history_repository = JsonHistoryRepository()
        self.router = ApplicationRouter(history_repository)

        # UI state
        self.current_view: Optional[str] = None
        self.last_game_result: Optional[GameResult] = None
        self.last_selected_game_index: int = 0  # Track which game was last played

    def compose(self) -> ComposeResult:
        """Create child widgets."""
        yield Header(show_clock=True)

        with Container(id="main-container"):
            # Main menu view
            yield MainMenuView(id="main-menu-view")

            # Game view (hidden initially)
            yield GameView(id="game-view")

            # Results view (hidden initially)
            yield ResultsView(id="results-view")

            # Stats view (hidden initially)
            yield StatsView(id="stats-view")

        # Input container for game input
        with Container(id="input-container"):
            yield Input(
                placeholder="Use arrow keys to navigate menu, ENTER to select",
                id="main-input",
            )

        yield Footer()

    def on_mount(self) -> None:
        """Event handler called when the app is mounted."""
        # Set theme for all components
        self._apply_theme_to_components()

        # Show main menu initially
        self._show_main_menu()

        # Focus the input
        self.query_one(Input).focus()

    def _apply_theme_to_components(self) -> None:
        """Apply theme to all UI components."""
        main_menu_view = self.query_one(MainMenuView)
        main_menu_view.set_theme(self.theme_name)

        game_view = self.query_one(GameView)
        game_view.set_theme(self.theme_name)

        results_view = self.query_one(ResultsView)
        results_view.set_theme(self.theme_name)

        stats_view = self.query_one(StatsView)
        stats_view.set_theme(self.theme_name)

    def _show_main_menu(self) -> None:
        """Show the main menu and hide other views."""
        self.current_view = "menu"
        self.router.return_to_main_menu()

        # Toggle view visibility
        self.query_one(MainMenuView).display = True
        self.query_one(GameView).display = False
        self.query_one(ResultsView).display = False
        self.query_one(StatsView).display = False

        # Update menu data
        self.query_one(MainMenuView).update_menu_data(
            {
                "title": "TermTypr - Typing Practice Games",
                "subtitle": "Choose a typing practice mode:",
                "games": self.router.get_available_games(),
                "selected_index": self.router.selected_game_index,
                "instructions": [
                    "Use ↑/↓ arrow keys or numbers to navigate",
                    "Press ENTER to select a game",
                    "Press 'Ctrl+Q' to quit",
                    "Press 'Ctrl+S' to view statistics",
                ],
            }
        )

        # Update and focus input
        input_field = self.query_one(Input)
        input_field.placeholder = (
            "Use arrow keys to navigate menu, ENTER to select, 'Ctrl+Q' to quit"
        )
        input_field.value = ""
        self.call_after_refresh(input_field.focus)

    def _show_game_view(self) -> None:
        """Show the game view and hide other views."""
        self.current_view = "game"

        # Toggle view visibility
        self.query_one(MainMenuView).display = False
        self.query_one(GameView).display = True
        self.query_one(ResultsView).display = False
        self.query_one(StatsView).display = False

        # Update input
        input_field = self.query_one(Input)
        input_field.placeholder = (
            "Type the words shown above... "
            "(SPACE to submit, → new words, ← retry same, ESC to restart, Ctrl+Q to quit)"
        )
        input_field.value = ""

    def _show_results_view(self, results: dict) -> None:
        """Show the results view with game results."""
        self.current_view = "results"

        # Toggle view visibility
        self.query_one(MainMenuView).display = False
        self.query_one(GameView).display = False
        self.query_one(ResultsView).display = True
        self.query_one(StatsView).display = False

        # Update results and input
        self.query_one(ResultsView).update_results(results)
        input_field = self.query_one(Input)
        input_field.placeholder = (
            "Press ENTER to play again, ESC for menu, Ctrl+Q to quit"
        )
        input_field.value = ""

    def on_key(self, event) -> None:
        """Handle key presses for menu navigation."""
        # Global key handlers first
        if event.key in ["ctrl+q", "ctrl+c"]:
            # Quit the application
            self.exit()
            return  # Context-specific key handlers
        if self.current_view == "menu":
            self._handle_menu_keys(event)
        elif self.current_view == "game":
            self._handle_game_keys(event)
        elif self.current_view == "results":
            self._handle_results_keys(event)
        elif self.current_view == "stats":
            self._handle_stats_keys(event)

    def _handle_menu_keys(self, event) -> None:
        """Handle key presses in main menu."""
        if event.key == "up":
            self.router.navigate_game_selection(-1)
            self._update_menu_display()
        elif event.key == "down":
            self.router.navigate_game_selection(1)
            self._update_menu_display()
        elif event.key == "ctrl+s":
            self._show_stats()

    def _handle_game_keys(self, event) -> None:
        """Handle key presses in game view."""
        if event.key == "right":
            # Skip to next game instance (new words/phrase)
            self._restart_current_game(keep_same_text=False)
        elif event.key == "left":
            # Restart with same words/phrase
            self._restart_current_game(keep_same_text=True)

    def _handle_results_keys(self, event) -> None:
        """Handle key presses in results view."""
        if event.key == "enter":
            # Restart same game when Enter is pressed
            input_field = self.query_one(Input)
            input_field.value = ""
            self._restart_current_game()

    def _handle_stats_keys(self, event) -> None:
        """Handle key presses in stats view."""
        if event.key == "escape":
            # Return to main menu
            self._show_main_menu()

    def _update_menu_display(self) -> None:
        """Update the menu display with current selection."""
        self.query_one(MainMenuView).update_menu_data(
            {
                "title": "TermTypr - Typing Practice Games",
                "subtitle": "Choose a typing practice mode:",
                "games": self.router.get_available_games(),
                "selected_index": self.router.selected_game_index,
                "instructions": [
                    "Use ↑/↓ arrow keys or numbers to navigate",
                    "Press ENTER to select a game",
                    "Press 'Ctrl+Q' to quit",
                    "Press 'Ctrl+S' to view statistics",
                ],
            }
        )

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle input submission."""
        input_value = event.input.value.strip()

        if self.current_view == "menu":
            # Start selected game
            self._start_selected_game()
        elif self.current_view == "game":
            # Process game input (only if not empty)
            if input_value:
                self._process_game_input(input_value)

    def on_input_changed(self, event: Input.Changed) -> None:
        """Handle real-time input changes for game."""
        if self.current_view != "game":
            return

        # Check if we have a game (don't require it to be active yet)
        if (
            not self.router.game_controller
            or not self.router.game_controller.current_game
        ):
            return

        input_text = event.input.value

        # Handle space bar for word completion
        if " " in input_text:
            self._process_game_input(input_text.strip(), is_complete=True)
            event.input.value = ""
            return

        # Process partial input for real-time feedback through the controller
        # This ensures game_state transitions to active on first character
        self.router.process_game_input(input_text, is_complete=False)
        self._update_game_display()

    def _start_selected_game(self) -> None:
        """Start the currently selected game."""
        # Save the selected game index for restart functionality
        self.last_selected_game_index = self.router.selected_game_index

        # Start game through router with default configuration
        if self.router.start_game():
            self._show_game_view()
            self._update_game_display()

            # Start update timer for stats
            self.set_interval(0.3, self._update_game_stats)

    def _process_game_input(self, word: str, is_complete: bool = True) -> None:
        """Process game input."""
        if not self.router.is_game_active():
            return

        self.router.process_game_input(word, is_complete)
        self._update_game_display()

        if is_complete:
            self.query_one(Input).value = ""

        # Check if game finished
        if self.router.game_controller.is_game_finished():
            self._finish_current_game()

    def _update_game_display(self) -> None:
        """Update the game display with current game state."""
        if not self.router.is_game_active():
            return

        display_data = self.router.get_game_display_data()
        if display_data:
            self.query_one(GameView).update_game_display(display_data)

    def _update_game_stats(self) -> None:
        """Update game statistics display."""
        if not self.router.is_game_active():
            return

        stats = self.router.get_game_stats()
        if not stats:
            return

        best_performance = self.router.stats_service.get_best_performance()
        best_wpm = best_performance.wpm if best_performance else 0.0
        self.query_one(GameView).update_game_stats(stats, best_wpm)

    def _finish_current_game(self) -> None:
        """Finish the current game and show results."""
        game_result = self.router.finish_game()
        if not game_result:
            return

        self.last_game_result = game_result

        # Prepare results dict with record comparison
        results = game_result.to_dict()
        results["is_new_record"] = game_result.is_new_record
        results["previous_best"] = game_result.previous_best

        self._show_results_view(results)

    def _restart_current_game(self, keep_same_text: bool = False) -> None:
        """Restart the current game.

        Args:
            keep_same_text: If True, restart with the same words/phrase.
                If False, generate new content.
        """
        # Save current target words if required
        saved_target_words = None
        if keep_same_text:
            if self.router.game_controller and self.router.game_controller.current_game:
                saved_target_words = (
                    self.router.game_controller.current_game.target_words.copy()
                )

        # Cancel and restart game
        if self.router.is_game_active():
            self.router.cancel_game()

        self.router.return_to_main_menu()
        self.router.select_game(self.last_selected_game_index)

        if self.router.start_game():
            # Restore saved words if we saved them
            if saved_target_words and self.router.game_controller.current_game:
                self.router.game_controller.current_game.target_words = (
                    saved_target_words
                )
                self.router.game_controller.game_state = GameState.create_ready(
                    target_words=saved_target_words
                )

            self._show_game_view()
            self._update_game_display()
            self.set_interval(0.3, self._update_game_stats)

    def _show_stats(self) -> None:
        """Show the statistics view with typing test records."""
        self.current_view = "stats"

        # Toggle view visibility
        self.query_one(MainMenuView).display = False
        self.query_one(GameView).display = False
        self.query_one(ResultsView).display = False
        self.query_one(StatsView).display = True

        # Update stats and input
        all_results = self.router.get_all_games(sort="asc")
        self.query_one(StatsView).update_records([r.to_dict() for r in all_results])

        input_field = self.query_one(Input)
        input_field.placeholder = "Press ESC to return to main menu, Ctrl+Q to quit"
        input_field.value = ""

    def action_main_menu(self) -> None:
        """Return to main menu."""
        if self.router.is_game_active():
            self.router.cancel_game()

        self._show_main_menu()

    def action_escape_action(self) -> None:
        """Handle escape key - context dependent."""
        if self.current_view == "game":
            # Restart if game started, otherwise return to menu
            if (
                self.router.game_controller
                and self.router.game_controller.game_state
                and self.router.game_controller.game_state.is_active
            ):
                self._restart_current_game(keep_same_text=True)
            else:
                self.action_main_menu()
        else:
            # Return to menu from results/stats views
            self._show_main_menu()


def run_new_app(theme: str = "default") -> None:
    """Run the new modular TermTypr application.

    Args:
        theme: Theme name to use.
    """
    app = TermTypr(theme_name=theme)
    app.run()
