"""Main menu view component."""

from typing import Any

from rich.align import Align
from rich.console import Group
from rich.panel import Panel
from rich.text import Text
from textual.widgets import Static

from src.config import THEMES


class MainMenuView(Static):
    """Widget for displaying the main menu."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.menu_data: dict[str, Any] = {}
        self.theme_colors = THEMES.get("default", THEMES["default"])

    def update_menu_data(self, menu_data: dict[str, Any]) -> None:
        """Update the menu data and refresh display."""
        self.menu_data = menu_data
        self.refresh()

    def set_theme(self, theme_name: str) -> None:
        """Set the theme for the menu."""
        self.theme_colors = THEMES.get(theme_name, THEMES["default"])
        self.refresh()

    def render(self) -> Panel:
        """Render the main menu."""
        if not self.menu_data:
            return Panel(
                Align.center(Text("Loading menu...", style="italic")),
                title="TermTypr",
                border_style=self.theme_colors["info"],
            )

        title_text = Text(self.menu_data.get("title", "TermTypr"), style="bold")
        subtitle_text = Text(self.menu_data.get("subtitle", ""), style="dim")

        game_items = []
        for game in self.menu_data.get("games", []):
            if game["is_selected"]:
                style = f"bold {self.theme_colors['current_word']}"
                prefix = "► "
            else:
                style = self.theme_colors["text"]
                prefix = "  "

            # Format: [index] Name - Description (shortcut)
            shortcut_part = (
                f" (Press '{game['shortcut_key']}')" if game.get("shortcut_key") else ""
            )
            game_line = f"{prefix}{game['index'] + 1}. {game['display_name']} - {game['description']}{shortcut_part}"

            game_items.append(Text(game_line, style=style))

        # Create instructions
        instructions = []
        for instruction in self.menu_data.get("instructions", []):
            instructions.append(Text(f"• {instruction}", style="dim"))

        # Combine all elements
        content_parts = [title_text, subtitle_text, Text("")]  # Empty line for spacing
        content_parts.extend(game_items)
        content_parts.append(Text(""))  # Empty line for spacing
        content_parts.extend(instructions)

        content = Group(*content_parts)

        return Panel(
            Align.center(content),
            title="Main Menu",
            border_style=self.theme_colors["info"],
            padding=(1, 2),
        )
