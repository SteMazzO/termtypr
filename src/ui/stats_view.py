"""Statistics view component for displaying typing test statistics with plotext charts."""

from datetime import datetime
from typing import Any

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
from textual.widgets import Static

from src.config import THEMES


class PlotextMixin(JupyterMixin):
    """Mixin class for integrating plotext with rich."""

    def __init__(self, width: int = 80, height: int = 20, title: str = ""):
        self.decoder = AnsiDecoder()
        self.width = width
        self.height = height
        self.title = title
        self.canvas = ""

    def __rich_console__(self, console, options):
        if self.canvas:
            self.rich_canvas = Group(*self.decoder.decode(self.canvas))
            yield self.rich_canvas


class StatsView(VerticalScroll):
    """Widget for displaying typing test statistics with scrolling and charts."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.records: list[dict[str, Any]] = []
        self.theme_colors = THEMES.get("default", THEMES["default"])

    def update_records(self, records: list[dict[str, Any]]) -> None:
        """Update the records data and refresh display."""
        self.records = records
        self._update_content()

    def set_theme(self, theme_name: str) -> None:
        """Set the theme for the stats view."""
        self.theme_colors = THEMES.get(theme_name, THEMES["default"])
        self._update_content()

    def compose(self) -> ComposeResult:
        """Compose the scrollable stats view."""
        yield Static(id="stats-content")

    def _update_content(self) -> None:
        """Update the content of the stats display."""
        content_widget = self.query_one("#stats-content", Static)
        content_widget.update(self._render_stats())

    def _create_wpm_trend_chart(
        self, width: int = 70, height: int = 15
    ) -> PlotextMixin:
        """Create a clean WPM trend chart using plotext."""
        plt.clf()
        plt.theme("dark")

        if len(self.records) < 2:
            plt.text("Start typing to see your progress!", 0.5, 0.5)
            plt.plotsize(width, height)
            plt.title("WPM Progress Chart")
            canvas = plt.build()
            mixin = PlotextMixin(width, height, "WPM Progress")
            mixin.canvas = canvas
            return mixin

        # Use last 20 tests for clean visualization
        recent_records = self.records[-20:] if len(self.records) > 20 else self.records
        x = list(range(1, len(recent_records) + 1))
        y = [record["wpm"] for record in recent_records]

        # Simple line chart with points
        plt.plot(x, y, color="cyan", marker="dot")

        plt.plotsize(width, height)
        plt.title(f"WPM Progress - Last {len(recent_records)} Tests")
        plt.xlabel("Test #")
        plt.ylabel("WPM")

        # Add min/max info
        min_wpm, max_wpm = min(y), max(y)
        plt.ylim(max(0, min_wpm - 5), max_wpm + 5)

        canvas = plt.build()
        mixin = PlotextMixin(width, height, "WPM Progress")
        mixin.canvas = canvas
        return mixin

    def _create_accuracy_chart(self, width: int = 70, height: int = 15) -> PlotextMixin:
        """Create a clean accuracy chart using plotext."""
        plt.clf()
        plt.theme("dark")

        if len(self.records) < 2:
            plt.text("Start typing to track accuracy!", 0.5, 0.5)
            plt.plotsize(width, height)
            plt.title("Accuracy Tracking")
            canvas = plt.build()
            mixin = PlotextMixin(width, height, "Accuracy Tracking")
            mixin.canvas = canvas
            return mixin

        recent_records = self.records[-20:] if len(self.records) > 20 else self.records
        x = list(range(1, len(recent_records) + 1))
        y = [record["accuracy"] for record in recent_records]

        # Simple line chart for accuracy
        plt.plot(x, y, color="green", marker="dot")

        plt.plotsize(width, height)
        avg_acc = sum(y) / len(y)
        plt.title(f"Accuracy Trend - Average: {avg_acc:.1f}%")
        plt.xlabel("Test #")
        plt.ylabel("Accuracy %")
        plt.ylim(max(0, min(y) - 5), 100)

        canvas = plt.build()
        mixin = PlotextMixin(width, height, "Accuracy Tracking")
        mixin.canvas = canvas
        return mixin

    def _create_performance_distribution(
        self, width: int = 70, height: int = 15
    ) -> PlotextMixin:
        """Create a clean WPM distribution histogram."""
        plt.clf()
        plt.theme("dark")

        if len(self.records) < 5:
            plt.text("Complete more tests for distribution!", 0.5, 0.5)
            plt.plotsize(width, height)
            plt.title("WPM Distribution")
            canvas = plt.build()
            mixin = PlotextMixin(width, height, "WPM Distribution")
            mixin.canvas = canvas
            return mixin

        wpm_values = [record["wpm"] for record in self.records]

        # Simple histogram
        plt.hist(wpm_values, bins=8, color="yellow")
        plt.plotsize(width, height)

        avg_wpm = sum(wpm_values) / len(wpm_values)
        plt.title(f"WPM Distribution - Average: {avg_wpm:.1f}")
        plt.xlabel("WPM Range")
        plt.ylabel("Count")

        canvas = plt.build()
        mixin = PlotextMixin(width, height, "WPM Distribution")
        mixin.canvas = canvas
        return mixin

    def _create_game_comparison_chart(
        self, width: int = 70, height: int = 15
    ) -> PlotextMixin:
        """Create a simple game comparison bar chart."""
        plt.clf()
        plt.theme("dark")

        game_stats = self._calculate_game_specific_stats()

        if len(game_stats) < 1:
            plt.text("No game data available!", 0.5, 0.5)
            plt.plotsize(width, height)
            plt.title("Game Comparison")
            canvas = plt.build()
            mixin = PlotextMixin(width, height, "Game Comparison")
            mixin.canvas = canvas
            return mixin

        # Sort by performance
        sorted_games = sorted(
            game_stats.items(), key=lambda x: x[1]["avg_wpm"], reverse=True
        )
        games = [g[0][:8] for g in sorted_games[:5]]  # Top 5 games, short names
        avg_wpms = [g[1]["avg_wpm"] for g in sorted_games[:5]]

        # Simple bar chart
        plt.bar(games, avg_wpms, color="magenta")
        plt.plotsize(width, height)
        plt.title("Game Mode Performance")
        plt.xlabel("Game")
        plt.ylabel("Avg WPM")

        canvas = plt.build()
        mixin = PlotextMixin(width, height, "Game Comparison")
        mixin.canvas = canvas
        return mixin

    def _create_recent_sessions_chart(
        self, width: int = 70, height: int = 15
    ) -> PlotextMixin:
        """Create a chart showing recent session performance."""
        plt.clf()
        plt.theme("dark")

        if len(self.records) < 5:
            plt.text("Complete more sessions to see trends!", 0.5, 0.5)
            plt.plotsize(width, height)
            plt.title("Recent Sessions")
            canvas = plt.build()
            mixin = PlotextMixin(width, height, "Recent Sessions")
            mixin.canvas = canvas
            return mixin

        # Get last 10 sessions
        recent = self.records[-10:]
        x = list(range(1, len(recent) + 1))
        wpm_data = [r["wpm"] for r in recent]
        acc_data = [r["accuracy"] for r in recent]

        # Plot WPM as main line
        plt.plot(x, wpm_data, color="cyan", marker="dot")

        # Normalize accuracy to WPM scale for dual axis effect
        max_wpm = max(wpm_data)
        normalized_acc = [acc * max_wpm / 100 for acc in acc_data]
        plt.plot(x, normalized_acc, color="green", marker="braille")

        plt.plotsize(width, height)
        plt.title("Recent Performance (Blue: WPM, Green: Accuracy)")
        plt.xlabel("Recent Tests")
        plt.ylabel("Performance")

        canvas = plt.build()
        mixin = PlotextMixin(width, height, "Recent Sessions")
        mixin.canvas = canvas
        return mixin

    def _render_stats(self) -> Group:
        """Render all statistics as a scrollable group with charts."""
        if not self.records:
            return Group(
                Panel(
                    Align.center(
                        Group(
                            Text("📊 No Statistics Available", style="bold"),
                            Text(""),
                            Text("No typing test records found.", style="dim"),
                            Text(
                                "Complete some typing tests to see your statistics here.",
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
                    border_style=self.theme_colors["info"],
                    padding=(1, 2),
                )
            )

        stats = self._calculate_stats()
        best_record = stats["best_record"]

        # Create sections as separate panels for better organization
        sections = []

        # Header
        sections.append(
            Panel(
                Text("📊 Typing Test Statistics", style="bold", justify="center"),
                border_style=self.theme_colors["info"],
            )
        )

        # Overview section
        overview_table = Table(show_header=False, box=None, padding=(0, 1))
        overview_table.add_column("Metric", style="dim")
        overview_table.add_column("Value", style="bold")
        overview_table.add_row("Total tests:", str(stats["total_tests"]))
        overview_table.add_row(
            "Total time:", self._format_duration(stats["total_time"])
        )
        overview_table.add_row("Average WPM:", f"{stats['avg_wpm']:.1f}")
        overview_table.add_row("Average accuracy:", f"{stats['avg_accuracy']:.1f}%")

        sections.append(
            Panel(
                overview_table,
                title="📈 Overview",
                border_style=self.theme_colors["info"],
            )
        )

        # WPM Trend Chart
        if len(self.records) >= 2:
            wpm_chart = self._create_wpm_trend_chart()
            sections.append(
                Panel(
                    wpm_chart,
                    title="📈 WPM Progress",
                    border_style=self.theme_colors["info"],
                )
            )

        # Accuracy Chart
        if len(self.records) >= 2:
            accuracy_chart = self._create_accuracy_chart()
            sections.append(
                Panel(
                    accuracy_chart,
                    title="🎯 Accuracy Tracking",
                    border_style=self.theme_colors["correct"],
                )
            )

        # Recent Sessions Chart
        if len(self.records) >= 5:
            recent_chart = self._create_recent_sessions_chart()
            sections.append(
                Panel(
                    recent_chart,
                    title="⚡ Recent Sessions",
                    border_style=self.theme_colors["info"],
                )
            )

        # Performance Distribution
        if len(self.records) >= 5:
            distribution_chart = self._create_performance_distribution()
            sections.append(
                Panel(
                    distribution_chart,
                    title="📊 WPM Distribution",
                    border_style=self.theme_colors["info"],
                )
            )

        # Best performance section
        best_table = Table(show_header=False, box=None, padding=(0, 1))
        best_table.add_column("Metric", style="dim")
        best_table.add_column("Value", style=f"bold {self.theme_colors['correct']}")
        best_table.add_row("Best WPM:", f"{best_record['wpm']:.1f}")
        best_table.add_row("Accuracy:", f"{best_record['accuracy']:.1f}%")
        best_table.add_row("Game:", best_record.get("game", "Unknown"))
        best_table.add_row("Date:", self._format_date(best_record["date"]))

        sections.append(
            Panel(
                best_table,
                title="🏆 Best Performance",
                border_style=self.theme_colors["correct"],
            )
        )

        # Game comparison chart
        game_stats = stats.get("game_stats", {})
        if len(game_stats) >= 1:
            game_chart = self._create_game_comparison_chart()
            sections.append(
                Panel(
                    game_chart,
                    title="🎮 Game Performance",
                    border_style=self.theme_colors["correct"],
                )
            )

        # Game-specific statistics table
        if game_stats:
            game_table = Table(show_header=True, header_style="bold")
            game_table.add_column("Game", style=f"{self.theme_colors['info']}")
            game_table.add_column("Tests", justify="center")
            game_table.add_column("Avg WPM", justify="center")
            game_table.add_column("Best WPM", justify="center")
            game_table.add_column("Accuracy", justify="center")
            game_table.add_column("Trend", justify="center")

            sorted_games = sorted(
                game_stats.items(), key=lambda x: x[1]["total_tests"], reverse=True
            )

            for game_name, game_data in sorted_games:
                if game_data["improvement"] > 0:
                    trend_icon = "↗"
                elif game_data["improvement"] < 0:
                    trend_icon = "↘"
                else:
                    trend_icon = "→"

                game_table.add_row(
                    game_name,
                    str(game_data["total_tests"]),
                    f"{game_data['avg_wpm']:.1f}",
                    f"{game_data['best_wpm']:.1f}",
                    f"{game_data['avg_accuracy']:.1f}%",
                    trend_icon,
                )

            sections.append(
                Panel(
                    game_table,
                    title="🎮 Game Statistics",
                    border_style=self.theme_colors["correct"],
                )
            )

        # Recent performance trend
        if stats["recent_count"] >= 3:
            trend_indicator = ""
            trend_style = "dim"
            if stats["recent_avg_wpm"] > stats["avg_wpm"]:
                trend_indicator = "↗ Improving!"
                trend_style = self.theme_colors["correct"]
            elif stats["recent_avg_wpm"] < stats["avg_wpm"] * 0.95:
                trend_indicator = "↘ Declining"
                trend_style = self.theme_colors["incorrect"]
            else:
                trend_indicator = "→ Stable"

            trend_content = Group(
                Text(
                    f"Recent average: {stats['recent_avg_wpm']:.1f} WPM", style="bold"
                ),
                Text(f"Trend: {trend_indicator}", style=trend_style),
                Text(
                    f"Based on last {stats['recent_count']} tests", style="dim italic"
                ),
            )

            sections.append(
                Panel(
                    trend_content,
                    title="🔥 Recent Trend",
                    border_style=self.theme_colors["info"],
                )
            )

        # Instructions
        sections.append(
            Panel(
                Group(
                    Text("💡 Navigation", style="bold", justify="center"),
                    Text(""),
                    Text(
                        "• Scroll up/down with arrow keys or mouse wheel", style="dim"
                    ),
                    Text("• Press ESC to return to main menu", style="dim"),
                    Text("• Press Ctrl+Q to quit application", style="dim"),
                ),
                border_style="dim",
            )
        )

        return Group(*sections)

    def _calculate_stats(self) -> dict[str, Any]:
        """Calculate comprehensive statistics from records."""
        if not self.records:
            return {}

        # Basic stats
        total_tests = len(self.records)
        best_record = max(self.records, key=lambda x: x.get("wpm", 0))

        # Averages
        avg_wpm = sum(record["wpm"] for record in self.records) / total_tests
        avg_accuracy = sum(record["accuracy"] for record in self.records) / total_tests
        avg_duration = sum(record["duration"] for record in self.records) / total_tests

        # Recent performance (last 5 tests)
        recent_records = self.records[-5:] if len(self.records) >= 5 else self.records
        recent_avg_wpm = sum(record["wpm"] for record in recent_records) / len(
            recent_records
        )
        recent_avg_accuracy = sum(
            record["accuracy"] for record in recent_records
        ) / len(recent_records)

        # Performance ranges
        wpm_values = [record["wpm"] for record in self.records]
        accuracy_values = [record["accuracy"] for record in self.records]

        min_wpm = min(wpm_values)
        max_wpm = max(wpm_values)
        min_accuracy = min(accuracy_values)
        max_accuracy = max(accuracy_values)

        # Total time spent
        total_time = sum(record["duration"] for record in self.records)

        # Game-specific stats
        game_stats = self._calculate_game_specific_stats()

        return {
            "total_tests": total_tests,
            "best_record": best_record,
            "avg_wpm": avg_wpm,
            "avg_accuracy": avg_accuracy,
            "avg_duration": avg_duration,
            "recent_avg_wpm": recent_avg_wpm,
            "recent_avg_accuracy": recent_avg_accuracy,
            "min_wpm": min_wpm,
            "max_wpm": max_wpm,
            "min_accuracy": min_accuracy,
            "max_accuracy": max_accuracy,
            "total_time": total_time,
            "recent_count": len(recent_records),
            "game_stats": game_stats,
        }

    def _calculate_game_specific_stats(self) -> dict[str, Any]:
        """Calculate statistics broken down by game type."""
        game_stats = {}

        # Group records by game type
        games_data = {}
        for record in self.records:
            game_name = record.get("game", "Unknown")
            if game_name not in games_data:
                games_data[game_name] = []
            games_data[game_name].append(record)

        # Calculate stats for each game
        for game_name, records in games_data.items():
            if not records:
                continue

            total_tests = len(records)
            avg_wpm = sum(r["wpm"] for r in records) / total_tests
            avg_accuracy = sum(r["accuracy"] for r in records) / total_tests
            best_wpm = max(r["wpm"] for r in records)
            best_accuracy = max(r["accuracy"] for r in records)
            total_time = sum(r["duration"] for r in records)

            # Calculate improvement trend (first half vs second half)
            if total_tests >= 4:
                mid_point = total_tests // 2
                first_half_avg = sum(r["wpm"] for r in records[:mid_point]) / mid_point
                second_half_avg = sum(r["wpm"] for r in records[mid_point:]) / (
                    total_tests - mid_point
                )
                improvement = second_half_avg - first_half_avg
            else:
                improvement = 0

            game_stats[game_name] = {
                "total_tests": total_tests,
                "avg_wpm": avg_wpm,
                "avg_accuracy": avg_accuracy,
                "best_wpm": best_wpm,
                "best_accuracy": best_accuracy,
                "total_time": total_time,
                "improvement": improvement,
                "latest_date": max(r["date"] for r in records),
            }

        return game_stats

    def _format_duration(self, seconds: float) -> str:
        """Format duration in a human-readable way."""
        if seconds < 60:
            return f"{seconds:.1f}s"

        if seconds < 3600:
            minutes = int(seconds // 60)
            remaining_seconds = seconds % 60
            return f"{minutes}m {remaining_seconds:.0f}s"

        hours = int(seconds // 3600)
        remaining_minutes = int((seconds % 3600) // 60)
        return f"{hours}h {remaining_minutes}m"

    def _format_date(self, date_str: str) -> str:
        """Format date string for display."""
        try:
            dt = datetime.fromisoformat(date_str)
            return dt.strftime("%Y-%m-%d")
        except (ValueError, AttributeError):
            return date_str.split("T")[0] if "T" in date_str else date_str

    def render(self) -> Panel:
        """Render the statistics display."""
        if not self.records:
            return Panel(
                Align.center(
                    Group(
                        Text("No Statistics Available", style="bold"),
                        Text(""),
                        Text("No typing test records found.", style="dim"),
                        Text(
                            "Complete some typing tests to see your statistics here.",
                            style="dim",
                        ),
                        Text(""),
                        Text("Press ESC to return to main menu", style="dim italic"),
                    )
                ),
                title="Statistics",
                border_style=self.theme_colors["info"],
                padding=(1, 2),
            )

        stats = self._calculate_stats()
        best_record = stats["best_record"]

        content_parts = []

        # Title
        content_parts.append(Text("Typing Test Statistics", style="bold"))
        content_parts.append(Text(""))

        # Overview section
        content_parts.extend(
            [
                Text("Overview", style=f"bold {self.theme_colors['info']}"),
                Text(f"Total tests completed: {stats['total_tests']}", style="dim"),
                Text(
                    f"Total time practiced: {self._format_duration(stats['total_time'])}",
                    style="dim",
                ),
                Text(""),
            ]
        )  # Best performance section
        best_game = best_record.get("game", "Unknown")
        content_parts.extend(
            [
                Text("Best Performance", style=f"bold {self.theme_colors['correct']}"),
                Text(
                    f"Best WPM: {best_record['wpm']:.1f} WPM ({best_game})",
                    style=self.theme_colors["info"],
                ),
                Text(
                    f"Accuracy: {best_record['accuracy']:.1f}%",
                    style=self.theme_colors["info"],
                ),
                Text(
                    f"Duration: {self._format_duration(best_record['duration'])}",
                    style=self.theme_colors["info"],
                ),
                Text(f"Date: {self._format_date(best_record['date'])}", style="dim"),
                Text(""),
            ]
        )

        # Average performance section
        content_parts.extend(
            [
                Text("Average Performance", style=f"bold {self.theme_colors['info']}"),
                Text(f"Average WPM: {stats['avg_wpm']:.1f}", style="dim"),
                Text(f"Average accuracy: {stats['avg_accuracy']:.1f}%", style="dim"),
                Text(
                    f"Average test duration: {self._format_duration(stats['avg_duration'])}",
                    style="dim",
                ),
                Text(""),
            ]
        )

        # Recent performance section (if enough tests)
        if stats["recent_count"] >= 3:
            trend_indicator = ""
            if stats["recent_avg_wpm"] > stats["avg_wpm"]:
                trend_indicator = " ↗ (improving!)"
                trend_style = self.theme_colors["correct"]
            elif stats["recent_avg_wpm"] < stats["avg_wpm"] * 0.95:  # 5% threshold
                trend_indicator = " ↘ (declining)"
                trend_style = self.theme_colors["incorrect"]
            else:
                trend_indicator = " → (stable)"
                trend_style = "dim"

            content_parts.extend(
                [
                    Text(
                        f"Recent Performance (last {stats['recent_count']} tests)",
                        style=f"bold {self.theme_colors['info']}",
                    ),
                    Text(
                        f"Recent avg WPM: {stats['recent_avg_wpm']:.1f}{trend_indicator}",
                        style=trend_style,
                    ),
                    Text(
                        f"Recent avg accuracy: {stats['recent_avg_accuracy']:.1f}%",
                        style="dim",
                    ),
                    Text(""),
                ]
            )  # Game-specific statistics section
        game_stats = stats.get("game_stats", {})
        if game_stats:
            content_parts.extend(
                [
                    Text(
                        "Game Statistics", style=f"bold {self.theme_colors['correct']}"
                    ),
                    Text(""),
                ]
            )

            # Sort games by total tests (most played first)
            sorted_games = sorted(
                game_stats.items(), key=lambda x: x[1]["total_tests"], reverse=True
            )

            for game_name, game_data in sorted_games:
                # Game name header
                content_parts.append(
                    Text(f"• {game_name}", style=f"bold {self.theme_colors['info']}")
                )

                # Game stats
                content_parts.extend(
                    [
                        Text(
                            f"  Tests: {game_data['total_tests']} | Avg WPM: {game_data['avg_wpm']:.1f} | Best: {game_data['best_wpm']:.1f}",
                            style="dim",
                        ),
                        Text(
                            f"  Avg Accuracy: {game_data['avg_accuracy']:.1f}% | Time: {self._format_duration(game_data['total_time'])}",
                            style="dim",
                        ),
                    ]
                )

                # Show improvement trend if available
                if game_data["improvement"] != 0:
                    if game_data["improvement"] > 0:
                        trend_text = (
                            f"  Improvement: +{game_data['improvement']:.1f} WPM ↗"
                        )
                        trend_style = self.theme_colors["correct"]
                    else:
                        trend_text = f"  Trend: {game_data['improvement']:.1f} WPM ↘"
                        trend_style = self.theme_colors["incorrect"]
                    content_parts.append(Text(trend_text, style=trend_style))

                content_parts.append(Text(""))

        # Performance range section
        content_parts.extend(
            [
                Text("Performance Range", style=f"bold {self.theme_colors['info']}"),
                Text(
                    f"WPM range: {stats['min_wpm']:.1f} - {stats['max_wpm']:.1f}",
                    style="dim",
                ),
                Text(
                    f"Accuracy range: {stats['min_accuracy']:.1f}% - {stats['max_accuracy']:.1f}%",
                    style="dim",
                ),
                Text(""),
            ]
        )

        # Instructions
        content_parts.extend(
            [
                Text("Press ESC to return to main menu", style="dim italic"),
                Text("Press Ctrl+Q to quit", style="dim italic"),
            ]
        )

        content = Group(*content_parts)

        return Panel(
            Align.center(content),
            title="Statistics",
            border_style=self.theme_colors["info"],
            padding=(1, 2),
        )
