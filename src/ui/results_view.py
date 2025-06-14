"""Results view component for displaying game results."""

from rich.align import Align
from rich.console import Group
from rich.panel import Panel
from rich.text import Text
from textual.widgets import Static

from src.config import THEMES


class ResultsView(Static):
    """Widget for displaying game results."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.results: dict[str, any] = {}
        self.theme_colors = THEMES.get("default", THEMES["default"])

    def update_results(self, results: dict[str, any]) -> None:
        """Update the results data and refresh display."""
        self.results = results
        self.refresh()

    def set_theme(self, theme_name: str) -> None:
        """Set the theme for the results view."""
        self.theme_colors = THEMES.get(theme_name, THEMES["default"])
        self.refresh()

    def render(self) -> Panel:
        """Render the results display."""
        if not self.results:
            return Panel(
                Align.center(Text("No results to display", style="italic")),
                title="Results",
                border_style=self.theme_colors["info"],
            )

        # Extract result data
        wpm = self.results.get("wpm", 0.0)
        accuracy = self.results.get("accuracy", 100.0)
        duration = self.results.get("duration", 0.0)
        is_new_record = self.results.get("is_new_record", False)
        previous_best = self.results.get("previous_best", 0.0)

        # Create result display
        content_parts = []

        # Title
        if is_new_record:
            content_parts.append(
                Text("🎉 NEW RECORD! 🎉", style=f"bold {self.theme_colors['correct']}")
            )
            content_parts.append(Text(""))
        else:
            content_parts.append(Text("Test Complete!", style="bold"))
            content_parts.append(Text(""))

        # Main statistics
        content_parts.extend(
            [
                Text(
                    f"Words Per Minute: {wpm:.1f} WPM",
                    style=f"bold {self.theme_colors['info']}",
                ),
                Text(
                    f"Accuracy: {accuracy:.1f}%",
                    style=f"bold {self.theme_colors['info']}",
                ),
                Text(
                    f"Time: {duration:.1f} seconds",
                    style=f"bold {self.theme_colors['info']}",
                ),
                Text(""),
            ]
        )

        # Record comparison
        if previous_best and previous_best > 0:
            if is_new_record:
                improvement = wpm - previous_best
                content_parts.extend(
                    [
                        Text("Record Comparison:", style="bold"),
                        Text(f"Previous best: {previous_best:.1f} WPM", style="dim"),
                        Text(
                            f"Improvement: +{improvement:.1f} WPM",
                            style=self.theme_colors["correct"],
                        ),
                        Text(""),
                    ]
                )
            else:
                deficit = previous_best - wpm
                content_parts.extend(
                    [
                        Text("Record Comparison:", style="bold"),
                        Text(f"Your best: {previous_best:.1f} WPM", style="dim"),
                        Text(
                            f"Difference: -{deficit:.1f} WPM",
                            style=self.theme_colors["incorrect"],
                        ),
                        Text(""),
                    ]
                )

        # Instructions
        content_parts.extend(
            [
                Text("Press ENTER to play again", style="dim italic"),
                Text("Press ESC to return to main menu", style="dim italic"),
                Text("Press Ctrl+Q to quit", style="dim italic"),
            ]
        )

        content = Group(*content_parts)

        border_style = (
            self.theme_colors["correct"] if is_new_record else self.theme_colors["info"]
        )

        return Panel(
            Align.center(content),
            title="Game Results",
            border_style=border_style,
            padding=(1, 2),
        )
