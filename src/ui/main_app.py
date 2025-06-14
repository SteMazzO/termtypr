"""New modular Textual application with menu system and game separation."""

from typing import Optional

from textual.app import App, ComposeResult
from textual.containers import Container
from textual.widgets import Footer, Header, Input

from src.config import THEMES
from src.data.history import HistoryManager
from src.games.base_game import GameStatus
from src.menu.menu_system import MenuSystem
from src.ui.game_view import GameView
from src.ui.main_menu_view import MainMenuView
from src.ui.results_view import ResultsView
from src.ui.stats_view import StatsView


class TermTypr(App):
    """Main application class with modular design and menu system."""

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

        # Initialize subsystems
        self.menu_system = MenuSystem()
        self.history_manager = HistoryManager()

        # UI state
        self.current_view: Optional[str] = None
        self.last_started_game_index: Optional[int] = None  # Track last started game

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

        # Reset menu system to ensure proper state
        self.menu_system.return_to_main_menu()  # Show main menu, hide others
        self.query_one(MainMenuView).display = True
        self.query_one(GameView).display = False
        self.query_one(ResultsView).display = False
        self.query_one(StatsView).display = False

        # Update menu data
        menu_data = self.menu_system.get_main_menu_data()
        main_menu_view = self.query_one(MainMenuView)
        main_menu_view.update_menu_data(menu_data)

        # Update input placeholder and clear input
        input_field = self.query_one(Input)
        input_field.placeholder = (
            "Use arrow keys to navigate menu, ENTER to select, 'q' to quit"
        )
        input_field.value = ""

        # Ensure input is focused
        self.call_after_refresh(input_field.focus)

    def _show_game_view(self) -> None:
        """Show the game view and hide other views."""
        self.current_view = "game"
        # Show game view, hide others
        self.query_one(MainMenuView).display = False
        self.query_one(GameView).display = True
        self.query_one(ResultsView).display = False
        self.query_one(StatsView).display = False

        # Update input placeholder
        input_field = self.query_one(Input)
        input_field.placeholder = (
            "Type the words shown above... (Press SPACE to submit word, 'q' to quit)"
        )
        input_field.value = ""

    def _show_results_view(self, results: dict) -> None:
        """Show the results view with game results."""
        self.current_view = "results"
        # Show results view, hide others
        self.query_one(MainMenuView).display = False
        self.query_one(GameView).display = False
        self.query_one(ResultsView).display = True
        self.query_one(StatsView).display = False

        # Update results data
        results_view = self.query_one(ResultsView)
        results_view.update_results(results)

        # Update input placeholder
        input_field = self.query_one(Input)
        input_field.placeholder = (
            "Press ENTER to play again, 'ESCAPE' for main menu, 'Ctrl+Q' to quit"
        )
        input_field.value = ""

    def on_key(self, event) -> None:
        """Handle key presses for menu navigation."""
        # Global key handlers first
        if event.key in ["ctrl+q", "ctrl+c"]:
            # Quit the application
            self.exit()
            return        # Context-specific key handlers
        if self.current_view == "menu":
            self._handle_menu_keys(event)
        elif self.current_view == "results":
            self._handle_results_keys(event)
        elif self.current_view == "stats":
            self._handle_stats_keys(event)

    def _handle_menu_keys(self, event) -> None:
        """Handle key presses in main menu."""
        if event.key == "up":
            self.menu_system.navigate_menu(-1)
            self._update_menu_display()
        elif event.key == "down":
            self.menu_system.navigate_menu(1)
            self._update_menu_display()
        elif event.key == "ctrl+s":
            self._show_stats()

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
        menu_data = self.menu_system.get_main_menu_data()
        main_menu_view = self.query_one(MainMenuView)
        main_menu_view.update_menu_data(menu_data)

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
        if self.current_view == "game" and self.menu_system.is_in_game():
            current_game = self.menu_system.get_current_game()
            if current_game:
                input_text = event.input.value

                # Handle space bar for word completion in word games
                if " " in input_text:
                    # Process as complete word
                    word = input_text.strip()
                    if word:
                        self._process_game_input(word, is_complete=True)
                        event.input.value = ""
                    return

                # Process partial input for real-time feedback
                current_game.process_input(input_text, is_complete_input=False)
                self._update_game_display()

    def _start_selected_game(self) -> None:
        """Start the currently selected game."""
        # For now, use default configuration
        # TODO: Add configuration dialog for games that need it
        if self.menu_system.start_selected_game():
            self.last_started_game_index = (
                self.menu_system.selected_menu_index
            )  # Save last started game
            self._show_game_view()
            self._update_game_display()

            # Start update timer for stats
            self.set_interval(0.3, self._update_game_stats)

    def _process_game_input(self, word: str, is_complete: bool = True) -> None:
        """Process game input."""
        if not self.menu_system.is_in_game():
            return

        current_game = self.menu_system.get_current_game()
        if not current_game:
            return

        result = current_game.process_input(word, is_complete_input=is_complete)

        # Update display
        self._update_game_display()

        # Clear input if word was completed
        if is_complete:
            input_field = self.query_one(Input)
            input_field.value = ""

        # Check if game is finished
        if result.get("status") == "complete" or current_game.is_finished():
            self._finish_current_game()

    def _update_game_display(self) -> None:
        """Update the game display with current game state."""
        if not self.menu_system.is_in_game():
            return

        current_game = self.menu_system.get_current_game()
        if not current_game:
            return

        # Update words display
        display_data = current_game.get_display_data()
        game_view = self.query_one(GameView)
        game_view.update_game_display(display_data)

    def _update_game_stats(self) -> None:
        """Update game statistics display."""
        if not self.menu_system.is_in_game():
            return

        current_game = self.menu_system.get_current_game()
        if not current_game:
            return

        # Get current stats
        stats = current_game.get_current_stats()

        # Get best record
        best_record = self.history_manager.get_best_record()
        best_wpm = best_record.get("wpm", 0.0) if best_record else 0.0

        # Update stats display
        game_view = self.query_one(GameView)
        game_view.update_game_stats(stats, best_wpm)

    def _finish_current_game(self) -> None:
        """Finish the current game and show results, with correct new record management."""
        results = self.menu_system.finish_current_game()
        if results:
            # After saving to history, check if this run is a new record
            history = self.history_manager.get_history()
            if history:
                previous_best = max((r["wpm"] for r in history[:-1]), default=None)
                is_new_record = results.get("wpm", 0) > (previous_best or 0)
            else:
                previous_best = None
                is_new_record = True

            results["is_new_record"] = is_new_record
            results["previous_best"] = previous_best
            self._show_results_view(results)

    def _restart_current_game(self) -> None:
        """Restart the current game with same settings."""
        # Cancel current game if in progress
        if self.menu_system.is_in_game():
            current_game = self.menu_system.get_current_game()
            if current_game:
                current_game.cancel()
        # Restore the menu to main state and select the last started game
        if self.last_started_game_index is not None:
            self.menu_system.return_to_main_menu()
            self.menu_system.select_game_by_index(self.last_started_game_index)
            self._start_selected_game()
        else:
            # Fallback to main menu if we don't know which game to restart
            self._show_main_menu()

    def _show_stats(self) -> None:
        """Show the statistics view with typing test records."""
        self.current_view = "stats"

        # Show stats view, hide others
        self.query_one(MainMenuView).display = False
        self.query_one(GameView).display = False
        self.query_one(ResultsView).display = False
        self.query_one(StatsView).display = True

        # Get all records and update stats view
        all_records = self.history_manager.get_history()
        stats_view = self.query_one(StatsView)
        stats_view.update_records(all_records)

        # Update input placeholder
        input_field = self.query_one(Input)
        input_field.placeholder = "Press ESC to return to main menu, Ctrl+Q to quit"
        input_field.value = ""

    def action_main_menu(self) -> None:
        """Return to main menu."""
        if self.menu_system.is_in_game():
            current_game = self.menu_system.get_current_game()
            if current_game:
                current_game.cancel()

        self.menu_system.return_to_main_menu()
        self._show_main_menu()

    def action_escape_action(self) -> None:
        """Handle escape key - context dependent."""
        if self.current_view == "game":
            current_game = self.menu_system.get_current_game()
            if current_game and current_game.status == GameStatus.ACTIVE:
                # Cancel current game and return to menu only if game has started
                self._restart_current_game()
            else:
                # Return to main menu
                self.action_main_menu()
        elif self.current_view == "results":
            # Return to main menu
            self._show_main_menu()
        elif self.current_view == "stats":
            # Return to main menu
            self._show_main_menu()


def run_new_app(theme: str = "default") -> None:
    """Run the new modular TermTypr application.

    Args:
        theme: Theme name to use.
    """
    app = TermTypr(theme_name=theme)
    app.run()
