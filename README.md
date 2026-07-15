# TermTypr

[![License: MIT](https://img.shields.io/github/license/SteMazzO/termtypr?logo=Open+Source+Initiative)](https://opensource.org/license/mit)
[![PyPI version](https://img.shields.io/pypi/v/termtypr?logo=pypi)](https://pypi.org/project/termtypr/)
[![PyPI Python](https://img.shields.io/pypi/pyversions/termtypr?logo=pypi)](https://pypi.org/project/termtypr/)
[![codecov](https://codecov.io/github/SteMazzO/termtypr/coverage.svg?branch=main)](https://codecov.io/github/SteMazzO/termtypr?branch=main)

Practice your typing right in the terminal. Track your speed, see where you improve, and have fun doing it.

## What it does

- **Three game modes** - random words, full phrases, or racing your own ghosts
- **Ghost racing** - replay your best phrase runs keystroke by keystroke and race against them
- **Live feedback** - WPM and accuracy update as you type
- **Stats & charts** - see your history, personal bests, and trends over time
- **Customizable** - set the word count per game, switch themes, add your own words
- **Runs anywhere** - works on any terminal with Python 3.10+

## Install and run

```bash
pip install termtypr
termtypr
```

That's it. The main menu lets you pick a game mode and start typing.

## Ghost racing

Finish a phrase run and TermTypr can save it as a **ghost** - a full replay of your
typing, corrections included. Race it two ways:

- **Instant rematch** - press `R` on the results screen to race the saved ghost of the
  phrase you just typed
- **Race a Ghost** - the menu mode picks one of your saved ghosts and races its phrase

During a race the ghost types in its own panel above yours, and the stats panel shows
how far ahead or behind you are. The race clock starts on your first keystroke, so take
your time getting ready.

By default the best run per phrase is saved automatically (up to a global cap, worst
runs pruned first). The command palette (`Ctrl+P`) has **Ghost Settings** for the save
mode - always ask, never, auto-best, or above a WPM threshold - and **Manage Ghosts**
to list and delete saved runs.

## CLI commands

```bash
termtypr                        # Launch the app
termtypr stats                  # Quick stats from the command line
termtypr add-words word1 word2  # Add your own words to the pool
termtypr list-words             # See all available words
```

## Development

### Setup Development Environment

```bash
git clone https://github.com/SteMazzO/termtypr.git
cd termtypr
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

### Run Tests

```bash
pytest tests/ -v
```

## Contributing

Contributions are welcome - see [CONTRIBUTING.md](CONTRIBUTING.md).

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Inspired by [MiType](https://github.com/Mithil467/mitype), [10FastFingers](https://10fastfingers.com/), and [TypeRacer](https://play.typeracer.com/)
- Text samples from [Typeracer Data](http://typeracerdata.com/texts)
- Built with [Textual](https://github.com/Textualize/textual) by Textualize

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history and release notes.
