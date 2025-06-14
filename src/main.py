"""Main entry point for the typing trainer application"""

import sys

from src.cli import app


def main():
    """Main entry point."""
    try:
        app()
    except KeyboardInterrupt:
        print("\nExiting...")
        sys.exit(0)
    except Exception as e:  # noqa
        print(f"Error: {e}")
        sys.exit(1)


# CLI entry point for use with pyproject.toml
def cli():
    """Entry point for CLI when installed via pip."""
    main()


if __name__ == "__main__":
    main()
