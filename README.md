# TermTypr

A modern, well-architected Python terminal application for practicing and improving typing speed with real-time feedback and comprehensive statistics.

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![PyPI version](https://badge.fury.io/py/termtypr.svg)](https://badge.fury.io/py/termtypr)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Features

- **Interactive Typing Tests** - Real-time WPM and accuracy tracking
- **Rich Statistics** - Detailed performance analytics with visual charts
- **Multiple Themes** - Light and dark visual themes
- **Game Modes** - Random words and phrase typing challenges
- **Record Tracking** - Personal best tracking with comparison
- **Persistent History** - All your typing sessions saved locally

## Quick Start

### Installation

```bash
pip install termtypr
```

### Run

```bash
termtypr
```

### CLI Commands

```bash
termtypr start              # Start the typing trainer
termtypr stats              # View statistics from command line
termtypr add-words word1    # Add custom words
termtypr list-words         # List all available words
```

## Development

### Setup Development Environment

```bash
git clone https://github.com/SteMazzO/termtypr.git
cd termtypr
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

### Run Tests

```bash
pytest tests/ -v           # Run all tests
pytest --cov=src tests/    # With coverage
```

## Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Inspired by [MiType](https://github.com/Mithil467/mitype), [10FastFingers](https://10fastfingers.com/), and [TypeRacer](https://play.typeracer.com/)
- Text samples from [Typeracer Data](http://typeracerdata.com/texts)
- Built with [Textual](https://github.com/Textualize/textual) by Textualize

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history and release notes.
