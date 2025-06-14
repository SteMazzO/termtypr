"""Command-line interface for the typing trainer application."""

import typer

from src.data.history import HistoryManager
from src.data.word_storage import WordStorage
from src.ui.main_app import run_new_app

app = typer.Typer(help="Fast typing trainer application")


# Set default function when no command is specified
@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    """TermTypr - A terminal-based typing practice application.

    If no command is provided, starts the main menu with typing games.
    """
    if ctx.invoked_subcommand is None:
        run_new_app(theme="default")


@app.command()
def start(
    theme: str = typer.Option(
        "default", "--theme", "-t", help="Theme to use (default or light)"
    ),
):
    """Start the typing trainer with main menu."""
    run_new_app(theme=theme)


@app.command()
def add_words(
    words: list[str] = typer.Argument(None, help="Words to add to the storage")  #  noqa
):
    """Add words to the word storage."""
    if not words:
        typer.echo("No words provided. Use: add_words word1 word2 word3 ...")
        return

    storage = WordStorage()
    result = storage.add_words(words)

    if result:
        typer.echo(f"Successfully added {len(words)} words to storage.")
    else:
        typer.echo("Failed to add words to storage.")


@app.command()
def stats():
    """Show typing test statistics."""
    hisotry_manager = HistoryManager()
    history = hisotry_manager.get_history()
    best_record = hisotry_manager.get_best_record()

    if not history:
        typer.echo("No typing test records found.")
        return

    typer.echo(f"Total tests: {len(history)}")

    if best_record:
        typer.echo(
            f"Best performance: {best_record['wpm']:.2f} WPM with "
            f"{best_record['accuracy']:.2f}% accuracy on {best_record['date'].split('T')[0]}"
        )

    # Calculate average stats
    avg_wpm = sum(record["wpm"] for record in history) / len(history)
    avg_accuracy = sum(record["accuracy"] for record in history) / len(history)

    typer.echo(
        f"Average performance: {avg_wpm:.2f} WPM with {avg_accuracy:.2f}% accuracy"
    )


@app.command()
def list_words():
    """List all available words in the storage."""
    storage = WordStorage()
    words = storage.get_words()

    if not words:
        typer.echo("No words found in storage.")
        return

    typer.echo(f"Total words in storage: {len(words)}")
    for i, word in enumerate(sorted(words)):
        typer.echo(f"  {i+1}. {word}")


def run():
    """Entry point for the CLI."""
    app()


if __name__ == "__main__":
    run()
