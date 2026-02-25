"""Statistics view for typing test results with plotext charts."""

from __future__ import annotations

import math
import statistics
from typing import TypedDict

import plotext as plt
from rich.align import Align
from rich.ansi import AnsiDecoder
from rich.console import Group
from rich.jupyter import JupyterMixin
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.events import Resize
from textual.widgets import Static

from termtypr.domain.models.game_result import GameResult


class _GameStats(TypedDict):
    total_tests: int
    avg_wpm: float
    avg_accuracy: float
    best_wpm: float
    trend_slope: float
    trend_window: int


class _StatsResult(TypedDict):
    total_tests: int
    best_record: GameResult
    avg_wpm: float
    avg_accuracy: float
    total_time: float
    recent_avg_wpm: float
    recent_count: int
    game_stats: dict[str, _GameStats]


class PlotextMixin(JupyterMixin):
    """Adapter that lets a plotext canvas render inside rich layouts."""

    def __init__(self) -> None:
        self.decoder = AnsiDecoder()
        self.canvas = ""

    def __rich_console__(self, console, options):  # noqa
        if self.canvas:
            yield Group(*self.decoder.decode(self.canvas))


_CHART_HEIGHT = 15
_MIN_CHART_WIDTH = 40
_DEFAULT_CHART_WIDTH = 70
_MIN_RECENT = 10
_TREND_WINDOW = 10


class StatsView(VerticalScroll):
    """Scrollable view that shows typing-test statistics and charts."""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.records: list[GameResult] = []
        self._valid_records: list[GameResult] = []

    def update_records(self, records: list[GameResult]) -> None:
        """Replace the records list and refresh the display."""
        self.records = records
        self._valid_records = [r for r in records if r.wpm > 0]
        self._update_content()

    def compose(self) -> ComposeResult:
        """Create the static content area for charts and stats."""
        yield Static(id="stats-content")

    def on_resize(self, event: Resize) -> None:
        """Re-render charts when the terminal is resized."""
        if self._valid_records:
            self._update_content()

    def _update_content(self) -> None:
        self.query_one("#stats-content", Static).update(self._render_stats())

    def _new_chart(self) -> None:
        """Reset plotext state for a fresh chart."""
        plt.clf()
        plt.theme("dark")

    @property
    def _chart_width(self) -> int:
        """Responsive chart width based on available container width."""
        available = self.size.width - 6 if self.size.width > 0 else _DEFAULT_CHART_WIDTH
        return max(_MIN_CHART_WIDTH, available)

    @property
    def _max_recent(self) -> int:
        """Number of recent tests to show, scaled with chart width."""
        return max(_MIN_RECENT, self._chart_width // 3)

    def _finalize_chart(self) -> PlotextMixin:
        """Build the current plotext figure and wrap it for rich rendering."""
        plt.plotsize(self._chart_width, _CHART_HEIGHT)
        mixin = PlotextMixin()
        mixin.canvas = plt.build()
        return mixin

    def _create_wpm_trend_chart(self) -> PlotextMixin:
        """Line chart of WPM over recent tests."""
        self._new_chart()

        recent = self._valid_records[-self._max_recent :]
        x = list(range(1, len(recent) + 1))
        y = [r.wpm for r in recent]

        plt.plot(x, y, color="cyan", marker="dot")
        plt.xlabel("Test #")
        plt.ylabel("WPM")
        plt.xticks(self._integer_ticks(x))

        lo, hi = min(y), max(y)
        plt.ylim(max(0, lo - 5), hi + 5)

        return self._finalize_chart()

    def _create_accuracy_chart(self) -> PlotextMixin:
        """Line chart of accuracy over recent tests."""
        self._new_chart()

        recent = self._valid_records[-self._max_recent :]
        x = list(range(1, len(recent) + 1))
        y = [r.accuracy for r in recent]

        plt.plot(x, y, color="green", marker="dot")
        plt.xlabel("Test #")
        plt.ylabel("Accuracy %")
        plt.xticks(self._integer_ticks(x))
        plt.ylim(max(0, min(y) - 5), 100)

        return self._finalize_chart()

    def _create_wpm_accuracy_chart(self) -> PlotextMixin:
        """Scatter plot of WPM vs Accuracy across all tests."""
        self._new_chart()

        x = [r.wpm for r in self._valid_records]
        y = [r.accuracy for r in self._valid_records]

        plt.scatter(x, y, color="cyan", marker="dot")
        plt.xlabel("WPM")
        plt.ylabel("Accuracy %")
        plt.ylim(max(0, min(y) - 5), 100)

        return self._finalize_chart()

    def _create_wpm_distribution_chart(self) -> PlotextMixin:
        """Histogram of WPM values."""
        self._new_chart()

        wpm_values = [r.wpm for r in self._valid_records]
        n_bins = 8

        plt.hist(wpm_values, bins=n_bins, color="yellow")
        plt.xlabel("WPM Range")
        plt.ylabel("Count")

        # Clamp x-axis so it never goes below 0
        lo, hi = min(wpm_values), max(wpm_values)
        plt.xlim(max(0, lo - 1), hi + 1)
        bin_width = (hi - lo) / n_bins if hi > lo else 1
        counts: list[int] = [0] * n_bins
        for v in wpm_values:
            idx = min(int((v - lo) / bin_width), n_bins - 1)
            counts[idx] += 1
        max_count = max(counts)
        step = max(1, math.ceil(max_count / 6))
        plt.yticks(list(range(0, max_count + step + 1, step)))

        return self._finalize_chart()

    def _create_game_comparison_chart(
        self, game_stats: dict[str, _GameStats]
    ) -> PlotextMixin:
        """Bar chart comparing average WPM per game mode."""
        self._new_chart()

        sorted_games = sorted(
            game_stats.items(), key=lambda x: x[1]["avg_wpm"], reverse=True
        )[:5]
        names = [g[0][:12] for g in sorted_games]
        avg_wpms = [g[1]["avg_wpm"] for g in sorted_games]

        plt.bar(names, avg_wpms, color="magenta")
        plt.xlabel("Game")
        plt.ylabel("Avg WPM")

        return self._finalize_chart()

    def _render_stats(self) -> Group:  # noqa
        """Build the full statistics display."""
        if not self._valid_records:
            return Group(
                Panel(
                    Align.center(
                        Group(
                            Text("\U0001f4ca No Statistics Available", style="bold"),
                            Text(""),
                            Text("No typing test records found.", style="dim"),
                            Text(
                                "Complete some tests to see your statistics here.",
                                style="dim",
                            ),
                            Text(""),
                            Text(
                                "Press ESC to return to main menu", style="dim italic"
                            ),
                            Text(
                                "Press Ctrl+Q to quit application", style="dim italic"
                            ),
                        )
                    ),
                    title="Statistics",
                    border_style="yellow",
                    padding=(1, 2),
                )
            )

        stats = self._calculate_stats()
        sections: list = []

        # ── Summary (overview + best + trend merged) ──
        summary_parts: list = []

        overview = Table(show_header=False, box=None, padding=(0, 2))
        overview.add_column("Metric", style="dim")
        overview.add_column("Value", style="bold")
        overview.add_column("Metric", style="dim")
        overview.add_column("Value", style="bold")
        overview.add_row(
            "Total tests:",
            str(stats["total_tests"]),
            "Total time:",
            self._format_duration(stats["total_time"]),
        )
        overview.add_row(
            "Average WPM:",
            f"{stats['avg_wpm']:.1f}",
            "Avg accuracy:",
            f"{stats['avg_accuracy']:.1f}%",
        )
        summary_parts.append(overview)
        summary_parts.append(Text(""))

        best: GameResult = stats["best_record"]
        summary_parts.append(
            Text(
                (
                    f"\U0001f3c6 Best: {best.wpm:.1f} WPM "
                    f"\u2022 {best.accuracy:.1f}% accuracy"
                ),
                style="bold green",
            )
        )
        summary_parts.append(
            Text(
                f"   {best.game_type} \u2022 {best.timestamp.strftime('%Y-%m-%d')}",
                style="dim",
            )
        )

        if stats["recent_count"] >= 3:
            trend = self._trend_indicator(stats["recent_avg_wpm"], stats["avg_wpm"])
            summary_parts.append(Text(""))
            summary_parts.append(
                Text(
                    f"\U0001f525 Recent: {stats['recent_avg_wpm']:.1f} WPM "
                    f"(last {stats['recent_count']}) {trend}",
                    style="bold",
                )
            )

        sections.append(
            Panel(
                Group(*summary_parts),
                title="\U0001f4ca Summary",
                border_style="yellow",
                padding=(1, 2),
            )
        )

        n_records = len(self._valid_records)
        n_recent = min(n_records, self._max_recent)

        if n_records >= 2:
            sections.append(
                Panel(
                    self._create_wpm_trend_chart(),
                    title=f"\U0001f4c8 WPM Progress \u2014 Last {n_recent} Tests",
                    border_style="yellow",
                )
            )
            sections.append(
                Panel(
                    self._create_accuracy_chart(),
                    title=f"\U0001f3af Accuracy Trend \u2014 Last {n_recent} Tests",
                    border_style="green",
                )
            )

        if n_records >= 3:
            sections.append(
                Panel(
                    self._create_wpm_accuracy_chart(),
                    title=(
                        f"\U0001f4c9 WPM vs Accuracy \u2014"
                        f" {stats['total_tests']} Tests"
                        f" (Avg: {stats['avg_accuracy']:.1f}%)"
                    ),
                    border_style="cyan",
                )
            )

        if n_records >= 5:
            sections.append(
                Panel(
                    self._create_wpm_distribution_chart(),
                    title=(
                        f"\U0001f4ca WPM Distribution "
                        f"\u2014 Average: {stats['avg_wpm']:.1f}"
                    ),
                    border_style="yellow",
                )
            )

        game_stats = stats.get("game_stats", {})

        if len(game_stats) >= 2:
            sections.append(
                Panel(
                    self._create_game_comparison_chart(game_stats),
                    title="\U0001f3ae Average WPM by Game Mode",
                    border_style="green",
                )
            )

        if game_stats:
            game_table = Table(show_header=True, header_style="bold")
            game_table.add_column("Game", style="yellow")
            game_table.add_column("Tests", justify="center")
            game_table.add_column("Avg WPM", justify="center")
            game_table.add_column("Best WPM", justify="center")
            game_table.add_column("Accuracy", justify="center")
            game_table.add_column("Trend", justify="center")

            for name, data in sorted(
                game_stats.items(),
                key=lambda x: x[1]["total_tests"],
                reverse=True,
            ):
                tw = data["trend_window"]
                if tw < 4:
                    trend_text = Text("\u2014", style="dim")
                else:
                    total_change = data["trend_slope"] * (tw - 1)
                    # 3% of avg WPM filters out normal variance
                    threshold = data["avg_wpm"] * 0.03
                    if total_change > threshold:
                        trend_text = Text(
                            f"\u2197 +{total_change:.1f} WPM (last {tw})",
                            style="green",
                        )
                    elif total_change < -threshold:
                        trend_text = Text(
                            f"\u2198 {total_change:.1f} WPM (last {tw})",
                            style="red",
                        )
                    else:
                        trend_text = Text("\u2192 Stable", style="dim")
                game_table.add_row(
                    name,
                    str(data["total_tests"]),
                    f"{data['avg_wpm']:.1f}",
                    f"{data['best_wpm']:.1f}",
                    f"{data['avg_accuracy']:.1f}%",
                    trend_text,
                )

            sections.append(
                Panel(
                    game_table, title="\U0001f3ae Game Statistics", border_style="green"
                )
            )

        sections.append(
            Text(
                "Scroll \u2191\u2193  \u2022  ESC menu  \u2022  Ctrl+Q quit",
                style="dim italic",
                justify="center",
            )
        )

        return Group(*sections)

    @staticmethod
    def _trend_indicator(recent_avg: float, overall_avg: float) -> str:
        """Classify the recent performance trend (symmetric \u00b13% band)."""
        if overall_avg == 0:
            return "\u2192 Stable"
        ratio = recent_avg / overall_avg
        if ratio > 1.03:
            return "\u2197 Improving"
        if ratio < 0.97:
            return "\u2198 Declining"
        return "\u2192 Stable"

    @staticmethod
    def _integer_ticks(values: list[int], max_ticks: int = 10) -> list[int]:
        """Return a subset of *values* spaced so at most *max_ticks* appear."""
        if len(values) <= max_ticks:
            return values
        step = len(values) // max_ticks + 1
        ticks = values[::step]
        if ticks[-1] != values[-1]:
            ticks.append(values[-1])
        return ticks

    def _calculate_stats(self) -> _StatsResult:
        """Compute aggregate statistics from records."""
        valid = self._valid_records
        n_valid = len(valid)
        best_record = max(valid, key=lambda r: r.wpm)

        avg_wpm = sum(r.wpm for r in valid) / n_valid
        avg_accuracy = sum(r.accuracy for r in valid) / n_valid
        total_time = sum(r.duration for r in self.records)

        recent = valid[-5:] if n_valid >= 5 else valid
        recent_avg_wpm = sum(r.wpm for r in recent) / len(recent)

        return {
            "total_tests": len(self.records),
            "best_record": best_record,
            "avg_wpm": avg_wpm,
            "avg_accuracy": avg_accuracy,
            "total_time": total_time,
            "recent_avg_wpm": recent_avg_wpm,
            "recent_count": len(recent),
            "game_stats": self._calculate_game_specific_stats(),
        }

    def _calculate_game_specific_stats(self) -> dict[str, _GameStats]:
        """Per-game breakdown of statistics."""
        groups: dict[str, list[GameResult]] = {}
        for r in self.records:
            groups.setdefault(r.game_type, []).append(r)

        game_stats: dict[str, _GameStats] = {}
        for name, results in groups.items():
            n = len(results)
            # Exclude scrap games (0 WPM) from averages and trend
            valid = [r for r in results if r.wpm > 0]
            n_valid = len(valid)

            if n_valid == 0:
                game_stats[name] = {
                    "total_tests": n,
                    "avg_wpm": 0.0,
                    "avg_accuracy": 0.0,
                    "best_wpm": 0.0,
                    "trend_slope": 0.0,
                    "trend_window": 0,
                }
                continue

            avg_wpm = sum(r.wpm for r in valid) / n_valid
            avg_accuracy = sum(r.accuracy for r in valid) / n_valid
            best_wpm = max(r.wpm for r in valid)

            if n_valid >= 4:
                # Linear regression on last N valid games gives a
                # responsive, organic trend (slope = WPM change/game).
                window = valid[-min(n_valid, _TREND_WINDOW) :]
                x = list(range(len(window)))
                y = [r.wpm for r in window]
                trend_slope = statistics.linear_regression(x, y).slope
                trend_window = len(window)
            else:
                trend_slope = 0.0
                trend_window = 0

            game_stats[name] = {
                "total_tests": n,
                "avg_wpm": avg_wpm,
                "avg_accuracy": avg_accuracy,
                "best_wpm": best_wpm,
                "trend_slope": trend_slope,
                "trend_window": trend_window,
            }

        return game_stats

    @staticmethod
    def _format_duration(seconds: float) -> str:
        """Format seconds into a human-readable string."""
        if seconds < 60:
            return f"{seconds:.0f}s"
        minutes, secs = divmod(int(seconds), 60)
        if minutes < 60:
            return f"{minutes}m {secs}s"
        hours, minutes = divmod(minutes, 60)
        return f"{hours}h {minutes}m"
