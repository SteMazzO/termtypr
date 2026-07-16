"""Game view component for displaying typing games."""

from typing import Any

from rich.align import Align
from rich.console import Group
from rich.panel import Panel
from rich.text import Text
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Static

from termtypr.domain.models.ghost_run import GhostRun


class TypedWordsDisplay(Static):
    """Base widget rendering target words styled by typing progress."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.words: list[str] = []
        self.typed_words: list[str] = []
        self.current_idx = 0
        self.current_input = ""

    def update_display_data(self, display_data: dict[str, Any]) -> None:
        """Update the display data from game or replay state."""
        self.words = display_data.get("target_words", [])
        self.typed_words = display_data.get("typed_words", [])
        self.current_idx = display_data.get("current_word_index", 0)
        self.current_input = display_data.get("current_input", "")

        self.refresh(layout=True)
        if self.parent:
            self.parent.refresh(layout=True)

    def styled_words_text(self) -> Text:
        """Build the words as one styled Text based on typing state."""
        text = Text()
        for i, word in enumerate(self.words):
            if i > 0:
                text.append(" ")
            text.append_text(self._get_styled_word(i, word))
        return text

    def _get_styled_word(self, i: int, word: str) -> Text:
        """Get styled word based on typing state."""
        if i < self.current_idx:
            # Completed word
            typed_word = self.typed_words[i] if i < len(self.typed_words) else ""
            style = "green" if typed_word == word else "red"
            return Text(word, style=style)

        if i == self.current_idx:
            # Current word being typed
            return self._get_current_word_style(word)

        # Future words
        return Text(word, style="dim")

    def _get_current_word_style(self, word: str) -> Text:
        """Style the current word being typed."""
        current_typed = (
            self.typed_words[self.current_idx]
            if self.current_idx < len(self.typed_words)
            else self.current_input
        )

        if not current_typed:
            return Text(word, style="cyan")

        # Find correct characters
        correct_chars = 0
        for j, char in enumerate(current_typed):
            if j < len(word) and char == word[j]:
                correct_chars += 1
            else:
                break

        # If a wrong character was typed, show the whole word as incorrect
        if correct_chars < len(current_typed):
            return Text(word, style="red")

        # Otherwise, show correct part and the rest as current_word
        word_text = Text()
        if correct_chars > 0:
            word_text.append(word[:correct_chars], style="green")
        if correct_chars < len(word):
            word_text.append(word[correct_chars:], style="cyan")
        return word_text


class GameWordsView(TypedWordsDisplay):
    """Widget for displaying typing words during a game."""

    def render(self) -> Panel:
        """Render the words display, responsive to panel width."""
        if not self.words:
            return Panel(
                Align.center(Text("Loading game...", style="italic")),
                title="Words",
                border_style="yellow",
            )

        return Panel(
            self.styled_words_text(),
            title="Words to Type",
            border_style="yellow",
            padding=(1, 2),
        )


class GhostWordsView(TypedWordsDisplay):
    """Widget replaying a ghost's typing during a race."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.ghost_wpm: float = 0.0
        self.finished_in: float | None = None

    def set_ghost(self, ghost: GhostRun) -> None:
        """Prepare the panel for a new race against the given ghost."""
        self.ghost_wpm = ghost.wpm
        self.finished_in = None
        self.words = ghost.phrase_text.split()
        self.typed_words = []
        self.current_idx = 0
        self.current_input = ""
        self.refresh(layout=True)

    def set_finished(self, duration: float) -> None:
        """Mark the ghost as done; shown in the panel title."""
        if self.finished_in != duration:
            self.finished_in = duration
            self.refresh()

    def render(self) -> Panel:
        """Render the ghost's replayed typing."""
        title = f"Ghost ({self.ghost_wpm:.1f} WPM)"
        if self.finished_in is not None:
            title += f" - finished in {self.finished_in:.1f}s"

        return Panel(
            self.styled_words_text(),
            title=title,
            border_style="magenta",
            padding=(1, 2),
        )


class GameStatsView(Static):
    """Widget for displaying game statistics."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.stats: dict[str, Any] = {}
        self.best_wpm: float = 0.0
        self.ghost_delta: float | None = None

    def update_stats(
        self,
        stats: dict[str, Any],
        best_wpm: float | None = None,
        ghost_delta: float | None = None,
    ) -> None:
        """Update the statistics display.

        Args:
            stats: Current game statistics.
            best_wpm: All-time best WPM shown for reference.
            ghost_delta: Seconds ahead (negative) or behind (positive) the
                ghost at the same progress; None when not racing.
        """
        self.stats = stats
        if best_wpm is not None:
            self.best_wpm = best_wpm
        self.ghost_delta = ghost_delta
        self.refresh()

    def _ghost_delta_text(self) -> Text:
        """Build the ahead/behind line shown while racing a ghost."""
        if self.ghost_delta is None:
            return Text("")
        if self.ghost_delta <= 0:
            return Text(f"Ghost: {-self.ghost_delta:.1f}s ahead", style="green")
        return Text(f"Ghost: {self.ghost_delta:.1f}s behind", style="red")

    def render(self) -> Panel:
        """Render the statistics display."""
        wpm = self.stats.get("wpm", 0.0) if self.stats else 0.0
        raw_wpm = self.stats.get("raw_wpm", 0.0) if self.stats else 0.0
        accuracy = self.stats.get("accuracy", 100.0) if self.stats else 0.0
        elapsed_time = self.stats.get("elapsed_time", 0.0) if self.stats else 0.0
        has_data = bool(self.stats)

        best_text = (
            Text(f"Best: {self.best_wpm:.1f} WPM", style="dim")
            if self.best_wpm > 0
            else Text("Best: -- WPM", style="dim")
        )

        content = Group(
            Text("Statistics", style="bold"),
            Text(""),
            Text(f"WPM: {wpm:.1f}" if has_data else "WPM: --", style="yellow"),
            Text(f"Raw: {raw_wpm:.1f}" if has_data else "Raw: --", style="dim"),
            Text(
                f"Accuracy: {accuracy:.1f}%" if has_data else "Accuracy: --",
                style="yellow",
            ),
            Text(
                f"Time: {elapsed_time:.1f}s" if has_data else "Time: --",
                style="yellow",
            ),
            Text(""),
            self._ghost_delta_text(),
            best_text,
        )

        return Panel(
            content,
            title="Stats",
            border_style="yellow",
            padding=(1, 1),
        )


class GameView(Container):
    """Main container for game display."""

    def compose(self) -> ComposeResult:
        """Create child widgets for game view.

        The ghost panel stacks above the player's words panel in one
        column, so both share the same width; the stats panel spans the
        full height on the right.
        """
        with Horizontal():
            with Vertical(id="game-words-column"):
                yield GhostWordsView(id="ghost-words-view")
                yield GameWordsView(id="game-words-view")
            yield GameStatsView(id="game-stats-view")

    def on_mount(self) -> None:
        """Hide the ghost panel until a race starts."""
        self.hide_ghost()

    def show_ghost(self, ghost: GhostRun) -> None:
        """Show the ghost panel, primed for a race against the given run."""
        ghost_view = self.query_one("#ghost-words-view", GhostWordsView)
        ghost_view.set_ghost(ghost)
        ghost_view.display = True

    def hide_ghost(self) -> None:
        """Hide the ghost panel (no race in progress)."""
        self.query_one("#ghost-words-view", GhostWordsView).display = False

    def update_ghost_display(
        self, display_data: dict[str, Any], finished_in: float | None = None
    ) -> None:
        """Update the ghost panel with replay state."""
        ghost_view = self.query_one("#ghost-words-view", GhostWordsView)
        ghost_view.update_display_data(display_data)
        if finished_in is not None:
            ghost_view.set_finished(finished_in)

    def update_game_display(self, display_data: dict[str, Any]) -> None:
        """Update the game display with new data."""
        words_view = self.query_one("#game-words-view", GameWordsView)
        words_view.update_display_data(display_data)

    def update_game_stats(
        self,
        stats: dict[str, Any],
        best_wpm: float | None = None,
        ghost_delta: float | None = None,
    ) -> None:
        """Update the game statistics display."""
        stats_view = self.query_one("#game-stats-view", GameStatsView)
        stats_view.update_stats(stats, best_wpm, ghost_delta)
