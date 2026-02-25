"""Results view component for displaying game results."""

from rich.align import Align
from rich.console import Group
from rich.panel import Panel
from rich.text import Text
from textual.widgets import Static

from termtypr.domain.models.game_result import GameResult


class ResultsView(Static):
    """Widget for displaying game results."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.result: GameResult | None = None

    def update_results(self, result: GameResult) -> None:
        """Update the results data and refresh display."""
        self.result = result
        self.refresh()

    def render(self) -> Panel:
        """Render the results display."""
        if not self.result:
            return Panel(
                Align.center(Text("No results to display", style="italic")),
                title="Results",
                border_style="yellow",
            )

        # Extract result data
        wpm = self.result.wpm
        accuracy = self.result.accuracy
        duration = self.result.duration
        is_new_record = self.result.is_new_record
        previous_best = self.result.previous_best or 0.0

        # Create result display
        content_parts = []

        # Title
        if is_new_record:
            content_parts.append(Text("🎉 NEW RECORD! 🎉", style="bold green"))
            content_parts.append(Text(""))
        else:
            content_parts.append(Text("Test Complete!", style="bold"))
            content_parts.append(Text(""))

        # Main statistics
        content_parts.extend(
            [
                Text(f"Words Per Minute: {wpm:.1f} WPM", style="bold yellow"),
                Text(f"Accuracy: {accuracy:.1f}%", style="bold yellow"),
                Text(f"Time: {duration:.1f} seconds", style="bold yellow"),
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
                            style="green",
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
                            style="red",
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

        border_style = "green" if is_new_record else "yellow"

        return Panel(
            Align.center(content),
            title="Game Results",
            border_style=border_style,
            padding=(1, 2),
        )
