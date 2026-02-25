# TermTypr

[![License: MIT](https://img.shields.io/github/license/SteMazzO/termtypr?logo=Open+Source+Initiative)](https://opensource.org/license/mit)
[![PyPI version](https://img.shields.io/pypi/v/termtypr?logo=pypi)](https://pypi.org/project/termtypr/)
[![PyPI Python](https://img.shields.io/pypi/pyversions/termtypr?logo=pypi)](https://pypi.org/project/termtypr/)
[![codecov](https://codecov.io/github/SteMazzO/termtypr/coverage.svg?branch=main)](https://codecov.io/github/SteMazzO/termtypr?branch=main)

Practice your typing right in the terminal. Track your speed, see where you improve, and have fun doing it.

## What it does

- **Two game modes** — random words or full phrases
- **Live feedback** — WPM and accuracy update as you type
- **Stats & charts** — see your history, personal bests, and trends over time
- **Customizable** — set the word count per game, switch themes, add your own words
- **Runs anywhere** — works on any terminal with Python 3.10+

## Install and run

```bash
pip install termtypr
termtypr
```

That's it. The main menu lets you pick a game mode and start typing.

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

Contributions are welcome — see [CONTRIBUTING.md](CONTRIBUTING.md).

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Inspired by [MiType](https://github.com/Mithil467/mitype), [10FastFingers](https://10fastfingers.com/), and [TypeRacer](https://play.typeracer.com/)
- Text samples from [Typeracer Data](http://typeracerdata.com/texts)
- Built with [Textual](https://github.com/Textualize/textual) by Textualize

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history and release notes.
