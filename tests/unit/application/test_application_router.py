"""Tests for ApplicationRouter."""

from datetime import datetime

import pytest

from src.application.router.application_router import (
    ApplicationRouter,
    AppScreen,
    GameDefinition,
)
from src.domain.models.game_result import GameResult
from src.games.phrase_typing_game import PhraseTypingGame
from src.games.random_words_game import RandomWordsGame
from src.infrastructure.persistence.memory_history_repository import (
    InMemoryHistoryRepository,
)


@pytest.fixture
def repository():
    """Create a memory repository for testing."""
    return InMemoryHistoryRepository()


@pytest.fixture
def router(repository):
    """Create an application router for testing."""
    return ApplicationRouter(repository)


@pytest.fixture
def populated_repository(repository):
    """Create a repository with some test data."""
    # Add some test results
    for i in range(5):
        result = GameResult(
            game_type="Random Words",
            wpm=50.0 + i * 5,
            accuracy=90.0 + i,
            duration=30.0,
            total_characters=150,
            correct_characters=140,
            error_count=10,
            timestamp=datetime.now(),
            is_new_record=i == 4,
        )
        repository.save(result)
    return repository


@pytest.fixture
def router_with_data(populated_repository):
    """Create a router with populated data."""
    return ApplicationRouter(populated_repository)


class TestRouterInitialization:
    """Tests for router initialization."""

    def test_initialization(self, router, repository):
        """Test router initializes correctly."""
        assert router.history_repository is repository
        assert router.stats_service is not None
        assert router.game_controller is None
        assert router.current_screen == AppScreen.MAIN_MENU
        assert router.selected_game_index == 0

    def test_available_games_loaded(self, router):
        """Test available games are loaded."""
        assert len(router.available_games) == 2
        assert router.available_games[0].name == "random_words"
        assert router.available_games[1].name == "phrase_typing"


class TestGameDefinition:
    """Tests for GameDefinition class."""

    def test_game_definition_creation(self):
        """Test creating a game definition."""
        game_def = GameDefinition(
            game_class=RandomWordsGame,
            name="test_game",
            display_name="Test Game",
            description="A test game",
        )

        assert game_def.game_class == RandomWordsGame
        assert game_def.name == "test_game"
        assert game_def.display_name == "Test Game"
        assert game_def.description == "A test game"

    def test_create_instance(self):
        """Test creating game instance from definition."""
        game_def = GameDefinition(
            game_class=RandomWordsGame,
            name="random_words",
            display_name="Random Words",
            description="Test",
        )

        instance = game_def.create_instance()
        assert isinstance(instance, RandomWordsGame)


class TestNavigation:
    """Tests for screen navigation."""

    def test_get_current_screen_initial(self, router):
        """Test getting initial screen."""
        assert router.get_current_screen() == AppScreen.MAIN_MENU

    def test_navigate_to_screen(self, router):
        """Test navigating to a valid screen."""
        result = router.navigate_to_screen(AppScreen.STATISTICS)
        assert result is True
        assert router.get_current_screen() == AppScreen.STATISTICS

    def test_navigate_to_game_active_without_game_fails(self, router):
        """Test navigating to game active without game fails."""
        result = router.navigate_to_screen(AppScreen.GAME_ACTIVE)
        assert result is False
        assert router.get_current_screen() == AppScreen.MAIN_MENU

    def test_return_to_main_menu(self, router):
        """Test returning to main menu."""
        router.navigate_to_screen(AppScreen.STATISTICS)
        router.return_to_main_menu()

        assert router.get_current_screen() == AppScreen.MAIN_MENU
        assert router.selected_game_index == 0

    def test_return_to_main_menu_cancels_active_game(self, router):
        """Test returning to menu cancels active game."""
        # Start a game
        router.select_game(0)
        router.start_game({"word_count": 5})

        assert router.is_game_active()

        # Return to main menu
        router.return_to_main_menu()

        assert not router.is_game_active()
        assert router.game_controller is None
        assert router.get_current_screen() == AppScreen.MAIN_MENU


class TestGameSelection:
    """Tests for game selection functionality."""

    def test_get_available_games(self, router):
        """Test getting available games list."""
        games = router.get_available_games()

        assert len(games) == 2
        assert games[0]["name"] == "random_words"
        assert games[0]["display_name"] == "Random Words"
        assert games[0]["is_selected"] is True
        assert games[1]["is_selected"] is False

    def test_select_game_valid_index(self, router):
        """Test selecting a game by valid index."""
        result = router.select_game(1)

        assert result is True
        assert router.selected_game_index == 1

    def test_select_game_invalid_index(self, router):
        """Test selecting a game by invalid index."""
        result = router.select_game(10)

        assert result is False
        assert router.selected_game_index == 0

    def test_navigate_game_selection_down(self, router):
        """Test navigating game selection down."""
        router.navigate_game_selection(1)

        assert router.selected_game_index == 1

    def test_navigate_game_selection_up(self, router):
        """Test navigating game selection up."""
        router.navigate_game_selection(-1)

        # Should wrap to last game
        assert router.selected_game_index == len(router.available_games) - 1

    def test_navigate_game_selection_wraps(self, router):
        """Test game selection wraps around."""
        router.select_game(1)  # Last game
        router.navigate_game_selection(1)  # Go down

        # Should wrap to first
        assert router.selected_game_index == 0

    def test_get_selected_game_definition(self, router):
        """Test getting selected game definition."""
        router.select_game(1)
        game_def = router.get_selected_game_definition()

        assert game_def is not None
        assert game_def.name == "phrase_typing"
        assert game_def.game_class == PhraseTypingGame


class TestGameLifecycle:
    """Tests for game lifecycle management."""

    def test_start_game_success(self, router):
        """Test starting a game successfully."""
        router.select_game(0)
        result = router.start_game({"word_count": 5})

        assert result is True
        assert router.game_controller is not None
        assert router.get_current_screen() == AppScreen.GAME_ACTIVE

    def test_start_game_with_default_config(self, router):
        """Test starting game with default config."""
        router.select_game(0)
        result = router.start_game()

        assert result is True
        assert router.game_controller is not None

    def test_start_game_invalid_selection(self, router):
        """Test starting game with invalid selection."""
        router.selected_game_index = 99  # Invalid
        result = router.start_game()

        assert result is False
        assert router.game_controller is None

    def test_is_game_active_no_game(self, router):
        """Test checking if game is active when no game."""
        assert router.is_game_active() is False

    def test_is_game_active_with_game(self, router):
        """Test checking if game is active with active game."""
        router.select_game(0)
        router.start_game({"word_count": 5})

        assert router.is_game_active() is True

    def test_process_game_input_no_game(self, router):
        """Test processing input without active game."""
        result = router.process_game_input("a")

        assert result is False

    def test_process_game_input_activates_game(self, router):
        """Test processing input activates game."""
        router.select_game(0)
        router.start_game({"word_count": 5})

        result = router.process_game_input("t")

        assert result is True

    def test_cancel_game(self, router):
        """Test cancelling a game."""
        router.select_game(0)
        router.start_game({"word_count": 5})

        result = router.cancel_game()

        assert result is True
        assert router.game_controller is None
        assert router.get_current_screen() == AppScreen.MAIN_MENU

    def test_cancel_game_no_active_game(self, router):
        """Test cancelling when no active game."""
        result = router.cancel_game()

        assert result is False

    def test_get_game_display_data_no_game(self, router):
        """Test getting display data without game."""
        data = router.get_game_display_data()

        assert data is None

    def test_get_game_display_data_with_game(self, router):
        """Test getting display data with active game."""
        router.select_game(0)
        router.start_game({"word_count": 5})

        data = router.get_game_display_data()

        assert data is not None
        assert "target_words" in data

    def test_get_game_stats_no_game(self, router):
        """Test getting stats without game."""
        stats = router.get_game_stats()

        assert stats is None

    def test_get_game_stats_with_game(self, router):
        """Test getting stats with active game."""
        router.select_game(0)
        router.start_game({"word_count": 5})
        router.process_game_input("t")  # Activate game

        stats = router.get_game_stats()

        assert stats is not None

    def test_finish_game_no_game(self, router):
        """Test finishing game when no game active."""
        result = router.finish_game()

        assert result is None


class TestStatisticsIntegration:
    """Tests for statistics integration."""

    def test_get_statistics_summary_empty(self, router):
        """Test getting statistics summary with no history."""
        summary = router.get_statistics_summary()

        assert "progress" in summary
        assert "best_performance" in summary
        assert "recent_games" in summary
        assert "game_type_stats" in summary

    def test_get_statistics_summary_with_data(self, router_with_data):
        """Test getting statistics summary with data."""
        summary = router_with_data.get_statistics_summary()

        assert summary["progress"]["total_games"] == 5
        assert summary["best_performance"] is not None
        assert len(summary["recent_games"]) == 5

    def test_get_recent_games(self, router_with_data):
        """Test getting recent games."""
        games = router_with_data.get_recent_games(limit=3)

        assert len(games) == 3

    def test_get_formatted_stats_table(self, router_with_data):
        """Test getting formatted stats table."""
        table = router_with_data.get_formatted_stats_table(limit=5)

        assert len(table) == 5
        assert "rank" in table[0]
        assert "wpm" in table[0]

    def test_clear_history(self, router_with_data):
        """Test clearing history."""
        # Verify we have data
        assert len(router_with_data.get_recent_games()) > 0

        # Clear
        result = router_with_data.clear_history()

        assert result is True
        assert len(router_with_data.get_recent_games()) == 0


class TestNavigationCleanup:
    """Tests for cleanup during navigation."""

    def test_leaving_game_active_to_main_menu_cleans_up(self, router):
        """Test that leaving game active screen cleans up controller."""
        # Start game
        router.select_game(0)
        router.start_game({"word_count": 5})

        # Navigate away
        router.navigate_to_screen(AppScreen.MAIN_MENU)

        # Controller should be cleaned up
        assert router.game_controller is None

    def test_leaving_game_active_to_results_keeps_controller(self, router):
        """Test that going to results screen keeps controller."""
        # Start game
        router.select_game(0)
        router.start_game({"word_count": 5})

        # Navigate to results
        router.navigate_to_screen(AppScreen.GAME_RESULTS)

        # Controller should still exist
        assert router.game_controller is not None
