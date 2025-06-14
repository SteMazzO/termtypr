# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]



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
