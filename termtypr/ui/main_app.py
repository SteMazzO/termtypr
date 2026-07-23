"""TermTypr Application."""

import time
from collections.abc import Iterable
from typing import TYPE_CHECKING

from textual.app import App, ComposeResult, SystemCommand
from textual.containers import Container, Horizontal, Vertical
from textual.screen import ModalScreen, Screen
from textual.widgets import (
    Button,
    DataTable,
    Footer,
    Header,
    Input,
    Label,
    Select,
    Static,
)

from termtypr.application.application_router import AVAILABLE_GAMES, ApplicationRouter
from termtypr.application.ghost_service import GhostService
from termtypr.config import save_preferences, user_preferences
from termtypr.core.ghost_replay import GhostReplay
from termtypr.domain.models.user_preferences import (
    GHOST_RUN_SIZE_KB,
    MAX_GHOST_WPM_THRESHOLD,
    MAX_GHOSTS_TOTAL,
    MAX_WORD_COUNT,
    MIN_GHOST_WPM_THRESHOLD,
    MIN_GHOSTS_TOTAL,
    MIN_WORD_COUNT,
    GhostSaveMode,
)
from termtypr.games.base_game import GameStatus
from termtypr.games.ghost_race_game import GhostRaceGame
from termtypr.infrastructure.persistence.sqlite_ghost_repository import (
    SqliteGhostRepository,
)
from termtypr.infrastructure.persistence.sqlite_history_repository import (
    SqliteHistoryRepository,
)
from termtypr.ui.game_view import GameView
from termtypr.ui.main_menu_view import MainMenuView
from termtypr.ui.results_view import ResultsView
from termtypr.ui.stats_view import StatsView

if TYPE_CHECKING:
    from termtypr.domain.models.game_result import GameResult

# Keep these short: they must fit the Select field on one line
GHOST_SAVE_MODE_LABELS = {
    GhostSaveMode.AUTO_BEST: "Auto: best per phrase",
    GhostSaveMode.AUTO_THRESHOLD: "Auto: above threshold",
    GhostSaveMode.ALWAYS_ASK: "Ask after each run",
    GhostSaveMode.NEVER: "Never save",
}


class WordCountDialog(ModalScreen[int | None]):
    """Modal dialog for setting the number of words per game."""

    CSS = """
    WordCountDialog {
        align: center middle;
    }

    #word-count-dialog {
        width: 50;
        height: auto;
        max-height: 16;
        border: thick $accent;
        background: $surface;
        padding: 1 2;
    }

    #word-count-dialog Label {
        margin-bottom: 1;
    }

    #wc-input {
        margin-bottom: 1;
    }

    #wc-error {
        color: $error;
        height: 1;
        margin-bottom: 1;
    }

    #wc-buttons {
        height: 3;
        align: center middle;
    }

    #wc-buttons Button {
        margin: 0 1;
    }
    """

    BINDINGS = [("escape", "cancel", "Cancel")]  # noqa

    def compose(self) -> ComposeResult:
        """Create the dialog layout."""
        with Vertical(id="word-count-dialog"):
            yield Label(f"Word Count  (current: {user_preferences.word_count})")
            yield Input(
                placeholder=f"{MIN_WORD_COUNT} - {MAX_WORD_COUNT}",
                value=str(user_preferences.word_count),
                id="wc-input",
                type="integer",
            )
            yield Static("", id="wc-error")
            with Horizontal(id="wc-buttons"):
                yield Button("OK", variant="primary", id="wc-ok")
                yield Button("Cancel", id="wc-cancel")

    def on_mount(self) -> None:
        """Focus the input field when the dialog is shown."""
        self.query_one("#wc-input", Input).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses for OK and Cancel."""
        event.stop()
        if event.button.id == "wc-ok":
            self._submit()
        else:
            self.dismiss(None)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle Enter key in the input field to submit."""
        # Stop the event here so it never reaches the app's handler,
        # which would treat it as menu/game input.
        event.stop()
        self._submit()

    def action_cancel(self) -> None:
        """Handle escape key to cancel the dialog."""
        self.dismiss(None)

    def _submit(self) -> None:
        """Validate the input and dismiss with the new word count if valid."""
        raw = self.query_one("#wc-input", Input).value.strip()
        error_label = self.query_one("#wc-error", Static)

        try:
            value = int(raw)
        except ValueError:
            error_label.update("Enter a whole number.")
            return

        if not MIN_WORD_COUNT <= value <= MAX_WORD_COUNT:
            error_label.update(
                f"Must be between {MIN_WORD_COUNT} and {MAX_WORD_COUNT}."
            )
            return

        self.dismiss(value)


class GhostSettingsDialog(ModalScreen[dict | None]):
    """Modal dialog for configuring ghost racing."""

    CSS = """
    GhostSettingsDialog {
        align: center middle;
    }

    #ghost-settings-dialog {
        width: 70;
        height: auto;
        border: thick $accent;
        background: $surface;
        padding: 1 2;
    }

    #gs-title {
        text-style: bold;
        margin-bottom: 1;
    }

    .gs-row {
        height: 3;
    }

    .gs-row Label {
        width: 28;
        padding: 1 0;
    }

    .gs-row Input, .gs-row Select {
        width: 1fr;
    }

    #gs-error {
        color: $error;
        height: 1;
    }

    #gs-buttons {
        height: 3;
        align: center middle;
    }

    #gs-buttons Button {
        margin: 0 1;
    }
    """

    BINDINGS = [("escape", "cancel", "Cancel")]  # noqa

    def compose(self) -> ComposeResult:
        """Create the dialog layout.

        Label/field pairs sit side by side: the dialog must stay short
        enough that the Save/Cancel buttons fit on a 24-line terminal.
        """
        disk_estimate_kb = user_preferences.max_ghosts_total * GHOST_RUN_SIZE_KB
        with Vertical(id="ghost-settings-dialog"):
            yield Label("Ghost Racing Settings", id="gs-title")
            with Horizontal(classes="gs-row"):
                yield Label("Save mode")
                yield Select(
                    [(label, mode) for mode, label in GHOST_SAVE_MODE_LABELS.items()],
                    value=user_preferences.ghost_save_mode,
                    allow_blank=False,
                    id="gs-mode",
                )
            with Horizontal(classes="gs-row"):
                yield Label("WPM threshold (auto mode)")
                yield Input(
                    value=f"{user_preferences.ghost_wpm_threshold:g}",
                    id="gs-threshold",
                    type="number",
                )
            with Horizontal(classes="gs-row"):
                yield Label("Min accuracy % (auto-save)")
                yield Input(
                    value=f"{user_preferences.ghost_min_accuracy:g}",
                    id="gs-accuracy",
                    type="number",
                )
            with Horizontal(classes="gs-row"):
                yield Label(f"Max ghosts (≈{disk_estimate_kb} KB)")
                yield Input(
                    value=str(user_preferences.max_ghosts_total),
                    id="gs-max",
                    type="integer",
                )
            yield Static("", id="gs-error")
            with Horizontal(id="gs-buttons"):
                yield Button("Save", variant="primary", id="gs-ok")
                yield Button("Cancel", id="gs-cancel")

    def on_mount(self) -> None:
        """Focus the first field when the dialog is shown."""
        self.query_one("#gs-mode", Select).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses for OK and Cancel."""
        event.stop()
        if event.button.id == "gs-ok":
            self._submit()
        else:
            self.dismiss(None)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle Enter key in any input field to submit."""
        # Stop the event here so it never reaches the app's handler,
        # which would treat it as menu/game input.
        event.stop()
        self._submit()

    def action_cancel(self) -> None:
        """Handle escape key to cancel the dialog."""
        self.dismiss(None)

    def _submit(self) -> None:
        """Validate the inputs and dismiss with the new settings if valid."""
        error_label = self.query_one("#gs-error", Static)

        try:
            threshold = float(self.query_one("#gs-threshold", Input).value)
            accuracy = float(self.query_one("#gs-accuracy", Input).value)
            max_ghosts = int(self.query_one("#gs-max", Input).value)
        except ValueError:
            error_label.update("All numeric fields must be filled in.")
            return

        if not MIN_GHOST_WPM_THRESHOLD <= threshold <= MAX_GHOST_WPM_THRESHOLD:
            error_label.update(
                f"WPM threshold must be between {MIN_GHOST_WPM_THRESHOLD:g} "
                f"and {MAX_GHOST_WPM_THRESHOLD:g}."
            )
            return
        if not 0 <= accuracy <= 100:
            error_label.update("Minimum accuracy must be between 0 and 100.")
            return
        if not MIN_GHOSTS_TOTAL <= max_ghosts <= MAX_GHOSTS_TOTAL:
            error_label.update(
                f"Max ghosts must be between {MIN_GHOSTS_TOTAL} and {MAX_GHOSTS_TOTAL}."
            )
            return

        self.dismiss(
            {
                "ghost_save_mode": self.query_one("#gs-mode", Select).value,
                "ghost_wpm_threshold": threshold,
                "ghost_min_accuracy": accuracy,
                "max_ghosts_total": max_ghosts,
            }
        )


class GhostManagerDialog(ModalScreen[None]):
    """Modal dialog listing saved ghosts, with delete support."""

    CSS = """
    GhostManagerDialog {
        align: center middle;
    }

    #ghost-manager-dialog {
        width: 90;
        max-width: 95%;
        height: auto;
        max-height: 30;
        border: thick $accent;
        background: $surface;
        padding: 1 2;
    }

    #gm-title {
        text-style: bold;
        margin-bottom: 1;
    }

    #gm-table {
        height: auto;
        max-height: 20;
    }

    #gm-hint {
        color: $text-muted;
        margin-top: 1;
    }
    """

    BINDINGS = [  # noqa
        ("escape", "close", "Close"),
        ("d", "delete_selected", "Delete"),
    ]

    def __init__(self, ghost_service: GhostService):
        super().__init__()
        self.ghost_service = ghost_service

    def compose(self) -> ComposeResult:
        """Create the dialog layout."""
        with Vertical(id="ghost-manager-dialog"):
            yield Label("Saved Ghosts", id="gm-title")
            yield DataTable(id="gm-table")
            yield Static(
                "Press D to delete the selected ghost, ESC to close", id="gm-hint"
            )

    def on_mount(self) -> None:
        """Populate the table with the saved ghosts."""
        table = self.query_one(DataTable)
        table.cursor_type = "row"
        table.add_columns("Phrase", "WPM", "Accuracy", "Time", "Saved")
        for ghost in self.ghost_service.repository.get_all():
            phrase = ghost.phrase_text
            excerpt = phrase if len(phrase) <= 60 else phrase[:59] + "…"
            table.add_row(
                excerpt,
                f"{ghost.wpm:.1f}",
                f"{ghost.accuracy:.1f}%",
                f"{ghost.duration:.1f}s",
                ghost.timestamp.strftime("%Y-%m-%d"),
                key=str(ghost.id),
            )
        table.focus()

    def action_close(self) -> None:
        """Close the dialog."""
        self.dismiss(None)

    def action_delete_selected(self) -> None:
        """Delete the ghost under the cursor."""
        table = self.query_one(DataTable)
        if table.row_count == 0:
            return

        row_key, _ = table.coordinate_to_cell_key(table.cursor_coordinate)
        if row_key.value is None:
            return
        if self.ghost_service.repository.delete(int(row_key.value)):
            table.remove_row(row_key)


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

    #game-words-column {
        width: 70%;
        margin: 0 1 0 0;
    }

    #ghost-words-view {
        height: auto;
        max-height: 50%;
        margin: 0 0 1 0;
    }

    #game-words-view {
        height: auto;
    }

    #game-stats-view {
        width: 30%;
        min-width: 25;
        margin: 0 0 0 1;
    }
    """

    BINDINGS = [  # noqa
        ("ctrl+q", "quit", "Quit"),
        ("escape", "escape_action", "Restart/Menu"),
    ]

    def __init__(self):
        """Initialize the application."""
        super().__init__()

        # Initialize application router with repositories
        history_repository = SqliteHistoryRepository()
        ghost_service = GhostService(SqliteGhostRepository())
        self.router = ApplicationRouter(history_repository, ghost_service)

        # UI state
        self.current_view: str | None = None
        self._stats_timer = None
        self._best_wpm: float = 0.0
        self._ghost_timer = None
        self._ghost_replay: GhostReplay | None = None
        self._last_ghost_frame: tuple | None = None

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
        # Show main menu initially
        self._show_main_menu()

        # Focus the input
        self.query_one(Input).focus()

    def _set_active_view(self, view_name: str) -> None:
        """Toggle visibility so only *view_name* is shown."""
        views = {
            "menu": MainMenuView,
            "game": GameView,
            "results": ResultsView,
            "stats": StatsView,
        }
        self.current_view = view_name
        for name, cls in views.items():
            self.query_one(cls).display = name == view_name

    def _get_menu_data(self) -> dict:
        """Build the menu data dict (used by show + update)."""
        return {
            "title": "TermTypr - Typing Practice Games",
            "subtitle": "Choose a typing practice mode:",
            "games": self.router.get_available_games(),
            "selected_index": self.router.selected_game_index,
            "instructions": [
                "Use ↑/↓ arrow keys or number keys to choose a game",
                "Press ENTER to start the selected game",
                "Press 'Ctrl+Q' to quit",
                "Press 'Ctrl+S' to view statistics",
            ],
        }

    def _show_main_menu(self) -> None:
        """Show the main menu and hide other views."""
        self._set_active_view("menu")
        self.router.return_to_main_menu()

        self.query_one(MainMenuView).update_menu_data(self._get_menu_data())

        input_field = self.query_one(Input)
        input_field.placeholder = (
            "Use arrow keys to navigate menu, ENTER to select, 'Ctrl+Q' to quit"
        )
        input_field.value = ""
        self.call_after_refresh(input_field.focus)

    def _show_game_view(self) -> None:
        """Show the game view and hide other views."""
        self._set_active_view("game")

        input_field = self.query_one(Input)
        input_field.placeholder = (
            "Type the words shown above... "
            "(SPACE to submit, → new words, ← or ESC to restart, Ctrl+Q to quit)"
        )
        input_field.value = ""

    def _show_results_view(self, result: "GameResult") -> None:
        """Show the results view with game results."""
        self._set_active_view("results")

        can_race_ghost = self.router.has_ghost_for_current_phrase()
        ghost_save_pending = self.router.has_pending_ghost_save()
        self.query_one(ResultsView).update_results(
            result,
            race_outcome=self.router.last_race_outcome,
            can_race_ghost=can_race_ghost,
            ghost_save_pending=ghost_save_pending,
            ghost_saved=self.router.last_ghost_saved,
        )

        placeholder = "Press ENTER to play again"
        if can_race_ghost:
            placeholder += ", R to race the ghost"
        if ghost_save_pending:
            placeholder += ", S to save as ghost"
        placeholder += ", ESC for menu, Ctrl+Q to quit"

        input_field = self.query_one(Input)
        input_field.placeholder = placeholder
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
            self.query_one(Input).value = ""
            self._restart_current_game()

    def _start_ghost_rematch(self) -> None:
        """Race the saved ghost of the phrase just played."""
        self.query_one(Input).value = ""
        if self.router.start_ghost_rematch():
            self._begin_game_session()
        else:
            self.notify("No ghost saved for this phrase", severity="warning")

    def _save_pending_ghost(self) -> None:
        """Save the finished run as a ghost when a decision is pending."""
        self.query_one(Input).value = ""
        if self.router.save_pending_ghost():
            self.notify("Run saved as ghost")
            # Re-render results: the save hint disappears, racing unlocks
            result = self.query_one(ResultsView).result
            if result is not None:
                self._show_results_view(result)

    def _update_menu_display(self) -> None:
        """Update the menu display with current selection."""
        self.query_one(MainMenuView).update_menu_data(self._get_menu_data())

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle input submission."""
        if event.input.id != "main-input":
            # Inputs in dialogs/modals are not mine to handle
            return

        input_value = event.input.value.strip()

        if self.current_view == "menu":
            # Start selected game
            self._start_selected_game()
        elif self.current_view == "game" and input_value:
            # Process game input (only if not empty)
            self._process_game_input(input_value)
            event.input.value = ""

    def on_input_changed(self, event: Input.Changed) -> None:
        """Handle real-time input changes for menu selection and game typing."""
        if event.input.id != "main-input":
            # Inputs in dialogs/modals are not mine to handle
            return

        if self.current_view == "menu":
            self._handle_menu_digit(event.input)
            return

        if self.current_view == "results":
            # Printable keys are consumed by the focused Input and never
            # reach on_key, so letter shortcuts arrive here instead
            self._handle_results_shortcut(event.input)
            return

        if self.current_view != "game":
            return

        # Check if we have a game (don't require it to be active yet)
        if not self.router.current_game:
            return

        input_text = event.input.value

        # Handle space bar for word completion
        if " " in input_text:
            self._submit_completed_words(input_text, event.input)
            return

        # Process partial input for real-time feedback through the controller
        # This ensures game_state transitions to active on first character
        self.router.process_game_input(input_text, is_complete=False)
        self._update_game_display()

        # The last word completes without a trailing space
        if self.router.is_game_finished():
            event.input.value = ""
            self._finish_current_game()

    def _handle_results_shortcut(self, input_field: Input) -> None:
        """Trigger results-view letter shortcuts typed into the input."""
        value = input_field.value.strip().lower()
        if not value:
            return

        input_field.value = ""
        if value == "r":
            self._start_ghost_rematch()
        elif value == "s":
            self._save_pending_ghost()

    def _handle_menu_digit(self, input_field: Input) -> None:
        """Select a menu entry when the user types its number."""
        value = input_field.value.strip()
        if not value:
            return

        if value.isdigit() and self.router.select_game(int(value) - 1):
            self._update_menu_display()

        # The input field is reserved for game typing; keep it empty in menu
        input_field.value = ""

    def _submit_completed_words(self, input_text: str, input_field: Input) -> None:
        """Submit space-terminated words, bare spaces never skip a word."""
        words = input_text.split()

        remainder = ""
        if words and not input_text.endswith(" "):
            remainder = words.pop()

        for word in words:
            if not self.router.is_game_active():
                break
            self._process_game_input(word, is_complete=True)

        if self.router.is_game_active():
            input_field.value = remainder

    def _start_selected_game(self) -> None:
        """Start the currently selected game."""
        if self.router.start_game():
            self._begin_game_session()
            return

        game_def = AVAILABLE_GAMES[self.router.selected_game_index]
        if game_def["game_class"] is GhostRaceGame:
            self.notify(
                "No ghosts saved yet - finish a phrase run first",
                severity="warning",
            )

    def _begin_game_session(self) -> None:
        """Common setup after a game starts: fetch best WPM, show view, start timer."""
        best = self.router.history_repository.get_best()
        self._best_wpm = best.wpm if best else 0.0
        self._show_game_view()
        self._update_game_display()
        self._start_stats_timer()
        self._setup_ghost_race()

    def _stop_stats_timer(self) -> None:
        """Stop the stats polling timer if running."""
        if self._stats_timer is not None:
            self._stats_timer.stop()
            self._stats_timer = None

    def _start_stats_timer(self) -> None:
        """Cancel any existing stats timer and start a fresh one."""
        self._stop_stats_timer()
        self._stats_timer = self.set_interval(0.3, self._update_game_stats)

    def _setup_ghost_race(self) -> None:
        """Start or clear the ghost replay to match the router's race state."""
        self._teardown_ghost_race()

        ghost = self.router.active_ghost
        game_view = self.query_one(GameView)
        if ghost is None:
            game_view.hide_ghost()
            return

        self._ghost_replay = GhostReplay(ghost)
        game_view.show_ghost(ghost)
        self._ghost_timer = self.set_interval(0.05, self._update_ghost_display)

    def _teardown_ghost_race(self) -> None:
        """Stop the ghost replay timer and drop the replay state."""
        if self._ghost_timer is not None:
            self._ghost_timer.stop()
            self._ghost_timer = None
        self._ghost_replay = None
        self._last_ghost_frame = None

    def _update_ghost_display(self) -> None:
        """Advance the ghost replay to the player's elapsed time."""
        if self._ghost_replay is None:
            return
        game = self.router.current_game
        if game is None:
            return

        # Before the player's first keystroke the race hasn't started:
        # freeze the replay before its t=0 event so nothing is revealed.
        elapsed = game.elapsed_seconds()
        elapsed_ms = -1 if elapsed is None else int(elapsed * 1000)

        state = self._ghost_replay.state_at(elapsed_ms)
        frame = (state.word_index, state.current_input, state.finished)
        if frame == self._last_ghost_frame:
            # Nothing moved since the last tick; skip the re-render
            return
        self._last_ghost_frame = frame

        finished_in = self._ghost_replay.ghost.duration if state.finished else None
        self.query_one(GameView).update_ghost_display(
            self._ghost_replay.display_data(state), finished_in
        )

    def _ghost_delta_seconds(self) -> float | None:
        """Seconds the player is behind (positive) or ahead of the ghost."""
        if self._ghost_replay is None:
            return None
        game = self.router.current_game
        if game is None:
            return None

        elapsed = game.elapsed_seconds()
        if elapsed is None:
            return None

        # Capped progress on both sides keeps the comparison fair even
        # when either typist over-typed a word
        ghost_ms = self._ghost_replay.time_to_reach_chars(game.progress_chars())
        if ghost_ms is None:
            # The ghost never covered this much; compare against its full run
            ghost_ms = int(self._ghost_replay.ghost.duration * 1000)
        return elapsed - ghost_ms / 1000

    def _process_game_input(self, word: str, is_complete: bool = True) -> None:
        """Process game input."""
        if not self.router.is_game_active():
            return

        self.router.process_game_input(word, is_complete)
        self._update_game_display()

        # Check if game finished
        if self.router.is_game_finished():
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

        self.query_one(GameView).update_game_stats(
            stats, self._best_wpm, self._ghost_delta_seconds()
        )

    def _finish_current_game(self) -> None:
        """Finish the current game and show results."""
        self._stop_stats_timer()
        self._teardown_ghost_race()
        game_result = self.router.finish_game()
        if not game_result:
            return

        self._show_results_view(game_result)

    def _restart_current_game(self, keep_same_text: bool = False) -> None:
        """Restart the current game.

        Args:
            keep_same_text: If True, restart with the same words/phrase.
                If False, generate new content.
        """
        if self.router.restart_game(keep_same_text=keep_same_text):
            self._begin_game_session()
            return

        # e.g. Race a Ghost when every ghost was deleted mid-session:
        # don't leave stale timers running against a dead game view
        self.notify("Could not restart the game", severity="warning")
        self.action_main_menu()

    def _show_stats(self) -> None:
        """Show the statistics view with typing test records."""
        # Reachable mid-game via the command palette
        self._stop_stats_timer()
        self._teardown_ghost_race()
        if self.router.is_game_active():
            self.router.cancel_game()

        self._set_active_view("stats")

        all_results = self.router.get_all_games(sort="asc")
        self.query_one(StatsView).update_records(all_results)

        input_field = self.query_one(Input)
        input_field.placeholder = "Press ESC to return to main menu, Ctrl+Q to quit"
        input_field.value = ""

    def get_system_commands(self, screen: Screen) -> Iterable[SystemCommand]:
        """Curated command palette entries for TermTypr."""
        if not self.ansi_color:
            yield SystemCommand(
                "Theme",
                "Change the current theme",
                self.action_change_theme,
            )

        yield SystemCommand(
            "Word Count",
            f"Set words per game (currently {user_preferences.word_count})",
            self._open_word_count_dialog,
        )

        yield SystemCommand(
            "Ghost Settings",
            "Configure ghost racing (save mode, thresholds, limits)",
            self._open_ghost_settings_dialog,
        )

        yield SystemCommand(
            "Manage Ghosts",
            "List and delete saved ghost runs",
            self._open_ghost_manager,
        )

        yield SystemCommand(
            "Statistics",
            "View your typing statistics",
            self._show_stats,
        )

        yield SystemCommand(
            "Main Menu",
            "Return to the main menu",
            self.action_main_menu,
        )

        yield SystemCommand(
            "Screenshot",
            "Save an SVG screenshot of the current screen",
            lambda: self.set_timer(0.1, self.deliver_screenshot),
        )

        yield SystemCommand(
            "Quit",
            "Quit the application",
            self.action_quit,
        )

    def _push_screen_pausing_run(self, screen: ModalScreen, callback=None) -> None:
        """Push a modal, pausing an active run's clock while it is open.

        Shifting start_time forward by the modal's lifetime pauses
        everything derived from the run clock at once: WPM stats, the
        ghost replay, the delta line, and recording timestamps.
        """
        game = self.router.current_game
        pause_started = (
            time.time()
            if self.current_view == "game" and game is not None and game.start_time
            else None
        )

        def _dismissed(result=None) -> None:
            if pause_started is not None and self.router.current_game is game:
                game.start_time += time.time() - pause_started
            if callback is not None:
                callback(result)

        self.push_screen(screen, callback=_dismissed)

    def _open_word_count_dialog(self) -> None:
        """Open the word-count modal and apply the result."""
        self._push_screen_pausing_run(
            WordCountDialog(), callback=self._on_word_count_result
        )

    def _on_word_count_result(self, value: int | None) -> None:
        """Callback when the word-count dialog is dismissed."""
        if value is None:
            return  # cancelled
        user_preferences.word_count = value
        save_preferences()
        self.notify(f"Word count set to {value}")

    def _open_ghost_settings_dialog(self) -> None:
        """Open the ghost-settings modal and apply the result."""
        self._push_screen_pausing_run(
            GhostSettingsDialog(), callback=self._on_ghost_settings_result
        )

    def _open_ghost_manager(self) -> None:
        """Open the saved-ghosts list modal."""
        if self.router.ghost_service is not None:
            self._push_screen_pausing_run(GhostManagerDialog(self.router.ghost_service))

    def _on_ghost_settings_result(self, values: dict | None) -> None:
        """Callback when the ghost-settings dialog is dismissed."""
        if values is None:
            return  # cancelled
        user_preferences.ghost_save_mode = values["ghost_save_mode"]
        user_preferences.ghost_wpm_threshold = values["ghost_wpm_threshold"]
        user_preferences.ghost_min_accuracy = values["ghost_min_accuracy"]
        user_preferences.max_ghosts_total = values["max_ghosts_total"]
        save_preferences()
        self.notify("Ghost settings saved")

    def action_main_menu(self) -> None:
        """Return to main menu."""
        self._stop_stats_timer()
        self._teardown_ghost_race()
        if self.router.is_game_active():
            self.router.cancel_game()

        self._show_main_menu()

    def action_escape_action(self) -> None:
        """Handle escape key - context dependent."""
        if self.current_view == "game":
            # Restart if started (ACTIVE),
            # otherwise return to menu (READY / no game).
            game = self.router.current_game
            if game and game.status == GameStatus.ACTIVE:
                self._restart_current_game(keep_same_text=True)
            else:
                self.action_main_menu()
        else:
            # Return to menu from results/stats views
            # (via action_main_menu so timers/games are cleaned up)
            self.action_main_menu()


def run_new_app() -> None:
    """Run the TermTypr application.

    Themes are managed by Textual's built-in theme system
    (Header settings icon, Ctrl+P command palette).
    """
    app = TermTypr()
    app.run()
