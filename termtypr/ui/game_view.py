"""Game view component for displaying typing games."""

from typing import Any

from rich.align import Align
from rich.console import Group
from rich.panel import Panel
from rich.text import Text
from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.widgets import Static


class GameWordsView(Static):
    """Widget for displaying typing words during a game."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.words: list[str] = []
        self.typed_words: list[str] = []
        self.current_idx = 0
        self.current_input = ""

    def update_display_data(self, display_data: dict[str, Any]) -> None:
        """Update the display data from game."""
        new_words = display_data.get("target_words", [])

        self.words = new_words
        self.typed_words = display_data.get("typed_words", [])
        self.current_idx = display_data.get("current_word_index", 0)
        self.current_input = display_data.get("current_input", "")

        self.refresh(layout=True)
        if self.parent:
            self.parent.refresh(layout=True)

    def render(self) -> Panel:
        """Render the words display, responsive to panel width."""
        if not self.words:
            return Panel(
                Align.center(Text("Loading game...", style="italic")),
                title="Words",
                border_style="yellow",
            )

        text = Text()
        for i, word in enumerate(self.words):
            if i > 0:
                text.append(" ")
            text.append_text(self._get_styled_word(i, word))

        return Panel(
            text,
            title="Words to Type",
            border_style="yellow",
            padding=(1, 2),
        )

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


class GameStatsView(Static):
    """Widget for displaying game statistics."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.stats: dict[str, Any] = {}
        self.best_wpm: float = 0.0

    def update_stats(
        self, stats: dict[str, Any], best_wpm: float | None = None
    ) -> None:
        """Update the statistics display."""
        self.stats = stats
        if best_wpm is not None:
            self.best_wpm = best_wpm
        self.refresh()

    def render(self) -> Panel:
        """Render the statistics display."""
        wpm = self.stats.get("wpm", 0.0) if self.stats else 0.0
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
            Text(
                f"Accuracy: {accuracy:.1f}%" if has_data else "Accuracy: --",
                style="yellow",
            ),
            Text(
                f"Time: {elapsed_time:.1f}s" if has_data else "Time: --",
                style="yellow",
            ),
            Text(""),
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
        """Create child widgets for game view."""
        with Horizontal():
            yield GameWordsView(id="game-words-view")
            yield GameStatsView(id="game-stats-view")

    def update_game_display(self, display_data: dict[str, Any]) -> None:
        """Update the game display with new data."""
        words_view = self.query_one("#game-words-view", GameWordsView)
        words_view.update_display_data(display_data)

    def update_game_stats(
        self, stats: dict[str, Any], best_wpm: float | None = None
    ) -> None:
        """Update the game statistics display."""
        stats_view = self.query_one("#game-stats-view", GameStatsView)
        stats_view.update_stats(stats, best_wpm)
