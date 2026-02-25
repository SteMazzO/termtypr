"""Command-line interface for the typing trainer application."""

import typer

from termtypr.data.word_storage import WordStorage
from termtypr.infrastructure.persistence.json_history_repository import (
    JsonHistoryRepository,
)
from termtypr.ui.main_app import run_new_app

app = typer.Typer(help="Fast typing trainer application")


# Set default function when no command is specified
@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    """TermTypr - A terminal-based typing practice application.

    If no command is provided, starts the main menu with typing games.
    """
    if ctx.invoked_subcommand is None:
        run_new_app()


@app.command()
def start():
    """Start the typing trainer with main menu."""
    run_new_app()


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
    repository = JsonHistoryRepository()
    all_results = repository.get_all()

    if not all_results:
        typer.echo("No typing test records found.")
        return

    typer.echo(f"Total tests: {len(all_results)}")

    valid = [r for r in all_results if r.wpm > 0]

    best = max(valid, key=lambda r: r.wpm) if valid else None
    if best:
        typer.echo(
            f"Best performance: {best.wpm:.1f} WPM with "
            f"{best.accuracy:.1f}% accuracy on {best.timestamp.strftime('%Y-%m-%d')}"
        )

    if valid:
        avg_wpm = sum(r.wpm for r in valid) / len(valid)
        avg_acc = sum(r.accuracy for r in valid) / len(valid)
        typer.echo(
            f"Average performance: {avg_wpm:.1f} WPM with {avg_acc:.1f}% accuracy"
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


if __name__ == "__main__":
    app()
