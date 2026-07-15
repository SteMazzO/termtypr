"""Results view component for displaying game results."""

from rich.align import Align
from rich.console import Group
from rich.panel import Panel
from rich.text import Text
from textual.widgets import Static

from termtypr.domain.models.game_result import GameResult
from termtypr.domain.models.ghost_run import RaceOutcome


class ResultsView(Static):
    """Widget for displaying game results."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.result: GameResult | None = None
        self.race_outcome: RaceOutcome | None = None
        self.can_race_ghost = False
        self.ghost_save_pending = False

    def update_results(
        self,
        result: GameResult,
        race_outcome: RaceOutcome | None = None,
        can_race_ghost: bool = False,
        ghost_save_pending: bool = False,
    ) -> None:
        """Update the results data and refresh display.

        Args:
            result: The finished game's result.
            race_outcome: Outcome of the ghost race, when one was run.
            can_race_ghost: True when this phrase has a saved ghost to race.
            ghost_save_pending: True when the run awaits a save decision.
        """
        self.result = result
        self.race_outcome = race_outcome
        self.can_race_ghost = can_race_ghost
        self.ghost_save_pending = ghost_save_pending
        self.refresh()

    def _race_outcome_parts(self) -> list[Text]:
        """Build the vs-ghost outcome lines, empty when no race was run."""
        outcome = self.race_outcome
        if outcome is None:
            return []

        delta = abs(outcome.delta_seconds)
        if outcome.won:
            headline = Text(f"You beat the ghost by {delta:.1f}s!", style="bold green")
        else:
            headline = Text(f"The ghost won by {delta:.1f}s", style="bold magenta")

        return [
            headline,
            Text(
                f"Ghost: {outcome.ghost.wpm:.1f} WPM in {outcome.ghost.duration:.1f}s",
                style="dim",
            ),
            Text(""),
        ]

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
        raw_wpm = self.result.raw_wpm
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

        # Ghost race outcome
        content_parts.extend(self._race_outcome_parts())

        # Main statistics
        content_parts.extend(
            [
                Text(f"Words Per Minute: {wpm:.1f} WPM", style="bold yellow"),
                Text(f"Raw (no error penalty): {raw_wpm:.1f} WPM", style="dim"),
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
        content_parts.append(Text("Press ENTER to play again", style="dim italic"))
        if self.can_race_ghost:
            content_parts.append(
                Text("Press R to race the ghost of this phrase", style="italic cyan")
            )
        if self.ghost_save_pending:
            content_parts.append(
                Text("Press S to save this run as a ghost", style="italic cyan")
            )
        content_parts.extend(
            [
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
