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
        self.ghost_saved = False

    def update_results(
        self,
        result: GameResult,
        race_outcome: RaceOutcome | None = None,
        can_race_ghost: bool = False,
        ghost_save_pending: bool = False,
        ghost_saved: bool = False,
    ) -> None:
        """Update the results data and refresh display.

        Args:
            result: The finished game's result.
            race_outcome: Outcome of the ghost race, when one was run.
            can_race_ghost: True when this phrase has a saved ghost to race.
            ghost_save_pending: True when the run awaits a save decision.
            ghost_saved: True when this run became the phrase's ghost.
        """
        self.result = result
        self.race_outcome = race_outcome
        self.can_race_ghost = can_race_ghost
        self.ghost_save_pending = ghost_save_pending
        self.ghost_saved = ghost_saved
        self.refresh()

    @staticmethod
    def _format_delta(delta: float) -> str:
        """Format a race time margin, keeping precision for close finishes."""
        return f"{delta:.2f}s" if delta < 1.0 else f"{delta:.1f}s"

    def _race_headline(self, outcome: RaceOutcome) -> Text:
        """One line saying who won the race and by how much."""
        margin = self._format_delta(abs(outcome.delta_seconds))
        if outcome.won:
            return Text(f"🏁 You beat the ghost by {margin}!", style="bold green")
        return Text(f"👻 The ghost wins by {margin}", style="bold magenta")

    def _race_comparison_table(self, outcome: RaceOutcome) -> Text:
        """Side-by-side You vs Ghost metrics, per-metric winner highlighted.

        Built as one multi-line Text so centering the panel content can't
        break the column alignment.
        """
        ghost = outcome.ghost
        rows = [
            # label, you, ghost, whether the player won this metric (None = tie)
            (
                "Time",
                f"{outcome.player_duration:.1f}s",
                f"{ghost.duration:.1f}s",
                outcome.player_duration < ghost.duration,
            ),
            (
                "WPM",
                f"{self.result.wpm:.1f}",
                f"{ghost.wpm:.1f}",
                self.result.wpm > ghost.wpm,
            ),
            (
                "Accuracy",
                f"{self.result.accuracy:.1f}%",
                f"{ghost.accuracy:.1f}%",
                self.result.accuracy > ghost.accuracy,
            ),
        ]

        table = Text()
        table.append(f"{'':<10}{'You':>9}{'Ghost':>9}", style="bold")
        for label, yours, ghosts, you_won in rows:
            tie = yours == ghosts
            table.append("\n")
            table.append(f"{label:<10}")
            table.append(
                f"{yours:>9}", style="" if tie else ("bold green" if you_won else "dim")
            )
            table.append(
                f"{ghosts:>9}",
                style="" if tie else ("magenta" if not you_won else "dim"),
            )
        return table

    def _race_outcome_parts(self) -> list:
        """Build the vs-ghost outcome block, empty when no race was run."""
        outcome = self.race_outcome
        if outcome is None:
            return []

        return [
            self._race_headline(outcome),
            Text(""),
            self._race_comparison_table(outcome),
            Text(""),
            Text(
                "Ghost: your best run from "
                f"{outcome.ghost.timestamp.strftime('%Y-%m-%d')}",
                style="dim",
            ),
            Text(f"Raw (no error penalty): {self.result.raw_wpm:.1f} WPM", style="dim"),
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

        # Title; in a race the headline carries the news instead
        if is_new_record:
            content_parts.append(Text("🎉 NEW RECORD! 🎉", style="bold green"))
            content_parts.append(Text(""))
        elif self.race_outcome is None:
            content_parts.append(Text("Test Complete!", style="bold"))
            content_parts.append(Text(""))

        if self.race_outcome is not None:
            # Race: the You-vs-Ghost table replaces the plain statistics
            content_parts.extend(self._race_outcome_parts())
        else:
            content_parts.extend(
                [
                    Text(f"Words Per Minute: {wpm:.1f} WPM", style="bold yellow"),
                    Text(f"Raw (no error penalty): {raw_wpm:.1f} WPM", style="dim"),
                    Text(f"Accuracy: {accuracy:.1f}%", style="bold yellow"),
                    Text(f"Time: {duration:.1f} seconds", style="bold yellow"),
                    Text(""),
                ]
            )

        if self.ghost_saved:
            content_parts.extend(
                [
                    Text(
                        "👻 This run is now the ghost to beat for this phrase",
                        style="cyan",
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
