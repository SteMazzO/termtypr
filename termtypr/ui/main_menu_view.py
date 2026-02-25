"""Main menu view component."""

from typing import Any

from rich.align import Align
from rich.console import Group
from rich.panel import Panel
from rich.text import Text
from textual.widgets import Static


class MainMenuView(Static):
    """Widget for displaying the main menu."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.menu_data: dict[str, Any] = {}

    def update_menu_data(self, menu_data: dict[str, Any]) -> None:
        """Update the menu data and refresh display."""
        self.menu_data = menu_data
        self.refresh()

    def render(self) -> Panel:
        """Render the main menu."""
        if not self.menu_data:
            return Panel(
                Align.center(Text("Loading menu...", style="italic")),
                title="TermTypr",
                border_style="yellow",
            )

        title_text = Text(self.menu_data.get("title", "TermTypr"), style="bold")
        subtitle_text = Text(self.menu_data.get("subtitle", ""), style="dim")

        game_items = []
        for game in self.menu_data.get("games", []):
            if game["is_selected"]:
                style = "bold cyan"
                prefix = "► "
            else:
                style = ""
                prefix = "  "

            game_line = (
                f"{prefix}{game['index'] + 1}. {game['display_name']}"
                " - "
                f"{game['description']}"
            )

            game_items.append(Text(game_line, style=style))

        # Create instructions
        instructions = [
            Text(f"• {instruction}", style="dim")
            for instruction in self.menu_data.get("instructions", [])
        ]

        # Combine all elements
        content_parts = [title_text, subtitle_text, Text("")]  # Empty line for spacing
        content_parts.extend(game_items)
        content_parts.append(Text(""))  # Empty line for spacing
        content_parts.extend(instructions)

        content = Group(*content_parts)

        return Panel(
            Align.center(content),
            title="Main Menu",
            border_style="yellow",
            padding=(1, 2),
        )
