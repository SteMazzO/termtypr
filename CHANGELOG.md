# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.5.0] - 2026-02-xx

### Added

- **User Preferences**: Persistent word count setting (JSON-based storage)
- **Command Palette**: Quick access to change word count, view statistics, and take screenshots
- **Statistics Enhancements**: WPM vs accuracy scatter plot

### Changed

- Simplified internal architecture, removed unnecessary layers and abstractions
- Flattened folder structure
- **Statistics accuracy**: Improved precision and formatting of displayed statistics
- **Statistics UI**: Improved layout and added responsive design
- **Trend display**: Shows total WPM change over trend window (e.g., `↗ +6.0 WPM (last 10)`)
- **Improved Performance**: Optimized data handling for a smoother user experience
- Cleaned up `pyproject.toml` lint rules and added multi-version test matrix (Python 3.10–3.14)

### Fixed

- **Timer leak**: Stats polling timer now reliably stopped on game finish/restart/menu return
- **New record logic**: 0 WPM games no longer trigger "NEW RECORD!" celebration

### Removed

- Removed unused code and dead modules

### Testing

- 61 unit tests, 100% passing, ruff fully clean on source and tests

## [0.4.1] - 2025-11-20

### Changed

- Rename `src` directory to `termtypr`

## [0.4.0] - 2025-11-19

### Added

- **Complete architectural overhaul**: Domain, Application, Infrastructure, and Presentation layers
- **Domain Models**: Immutable `GameResult`, `GameState`, `TypingStats` value objects
- **Repository Pattern**: Abstract `HistoryRepository` with JSON and in-memory implementations
- **Application Services**: `GameController`, `StatsService`, `ApplicationRouter`
- **Enhanced UX**: Same-content restart
- **Type Safety**: Pydantic settings, full type hints, immutable dataclasses

### Changed

- **UI Layer**: Replaced `MenuSystem` with `ApplicationRouter`, views are pure presentation
- **Game System**: History management moved from `BaseGame` to `GameController`
- **CLI**: Updated `stats` command to use new architecture
- **Settings**: Migrated to Pydantic for validation

### Removed

- **Legacy Code**: `MenuSystem`, legacy `HistoryManager`, `history_adapter.py`

### Testing

- 136 unit tests, 100% passing

## [0.3.5] - 2025-08-28

### Changed

- Trim word list

### Fixed

- WPM Calculation

## [0.3.4] - 2025-06-19

### Fixed

- fix: cap typo count to prevent negative accuracy calculation
- fix: resolve word panel resizing issues

### Changed

- refactor: simplify game classes & remove redundant code

## [0.3.3] - 2025-06-18

### Fixed

- fix: correctly load phrases from package data
- fix: do not display errors in words panel when typing incorrect letters
- fix: allow skipping current word by pressing space on empty input

## [0.3.2] - 2025-06-14

### Fixed

- Fixed build configuration to correctly include resource files in wheel package

## [0.3.1] - 2025-06-14

### Fixed

- Fixed data files not being included when installing from PyPI
- Moved history storage to user's data directory using platformdirs
- Added proper package data configuration in pyproject.toml

## [0.3.0] - 2025-06-14

### Added

- **New Phrase Typing Game**: Complete phrase typing experience with literary quotes and meaningful texts
- **Enhanced Statistics System**: Comprehensive statistics view with interactive charts and graphs using plotext library
- **Visual Data Analytics**:
  - WPM progress trend charts showing typing improvement over time
  - Accuracy tracking charts with performance analysis
  - Game comparison bar charts for performance across different typing modes
  - Performance distribution histograms showing WPM ranges
  - Recent sessions charts with dual-axis WPM and accuracy visualization
- **Scrollable Statistics Interface**: The statistics view is now scrollable!

### Enhanced

- **Game Architecture**: Improved base game system supproting multiple typing game types with unified interface

### Fixed

- **Word Panel Layout Issues**: Resolved word panel resizing problems with responsive terminal layout handling
- **UI Refresh Logic**: Improved layout refresh mechanism ensuring proper display updates during game state changes
- **Statistics Display**: Better formatting and organization of statistical data with clear visual separation

## [0.2.0] - 2025-05-25

### Added

- New main menu system, allowing users ti navigate and select between different games and views.
- Comprehensive statistics view accessible from the main menu, with detailed stats and trends.
- New `HistoryManager` for robust run history and statistics (replacing `RecordsManager`).

### Fixed

- Fixed bug where words could be hidden in the words panel; words now wrap responsively to the terminal/panel size, ensuring all are visible.
- Improved UI state transitions and key handling for the new stats view.

## [0.1.0] - 2025-05-11

### Added

- Terminal-based text user interface
- Real-time typing statistics (WPM, accuracy, time)
- Records system to track typing performance

### Features

- Real-time character-by-character feedback as you type
- Dynamic WPM/Accuracy calculation
- Clean, responsive terminal UI
- Support for various terminal themes
