"""Tests for ApplicationRouter."""

from datetime import datetime, timezone

import pytest

from termtypr.application.application_router import AVAILABLE_GAMES, ApplicationRouter
from termtypr.application.ghost_service import GhostService
from termtypr.config import user_preferences
from termtypr.domain.models.game_result import GameResult
from termtypr.domain.models.user_preferences import DEFAULT_WORD_COUNT, UserPreferences
from termtypr.games.base_game import GameStatus
from termtypr.infrastructure.persistence.memory_history_repository import (
    InMemoryHistoryRepository,
)
from termtypr.infrastructure.persistence.sqlite_ghost_repository import (
    SqliteGhostRepository,
)
from termtypr.infrastructure.persistence.sqlite_history_repository import (
    SqliteHistoryRepository,
)


@pytest.fixture
def repository():
    """Create a memory repository for testing."""
    return InMemoryHistoryRepository()


@pytest.fixture(autouse=True)
def _reset_preferences():
    """Ensure user_preferences has deterministic defaults for every test."""
    defaults = UserPreferences()
    saved = user_preferences.model_dump()
    for key in saved:
        setattr(user_preferences, key, getattr(defaults, key))
    yield
    for key, value in saved.items():
        setattr(user_preferences, key, value)


@pytest.fixture
def router(repository):
    """Create an application router for testing."""
    return ApplicationRouter(repository)


@pytest.fixture
def populated_repository(repository):
    """Create a repository with some test data."""
    for i in range(5):
        result = GameResult(
            game_type="Random Words",
            wpm=50.0 + i * 5,
            accuracy=90.0 + i,
            duration=30.0,
            total_characters=150,
            correct_characters=140,
            error_count=10,
            timestamp=datetime.now(tz=timezone.utc),
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
        assert router.current_game is None
        assert router.selected_game_index == 0

    def test_available_games_loaded(self, router):
        """Test available games are loaded."""
        assert len(AVAILABLE_GAMES) == 2
        assert AVAILABLE_GAMES[0]["name"] == "RandomWordsGame"
        assert AVAILABLE_GAMES[1]["name"] == "PhraseTypingGame"


class TestGameSelection:
    """Tests for game selection functionality."""

    def test_get_available_games(self, router):
        """Test getting available games list."""
        games = router.get_available_games()

        assert len(games) == 2
        assert games[0]["name"] == "RandomWordsGame"
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
        assert router.selected_game_index == len(AVAILABLE_GAMES) - 1

    def test_navigate_game_selection_wraps(self, router):
        """Test game selection wraps around."""
        router.select_game(1)  # Last game
        router.navigate_game_selection(1)  # Go down

        # Should wrap to first
        assert router.selected_game_index == 0


class TestGameLifecycle:
    """Tests for game lifecycle management."""

    def test_start_game_success(self, router):
        """Test starting a game successfully."""
        router.select_game(0)
        result = router.start_game({"word_count": 5})

        assert result is True
        assert router.current_game is not None
        assert router.current_game.status == GameStatus.READY
        assert len(router.current_game.target_words) == 5

    def test_start_game_with_default_config(self, router):
        """Test starting game with default config."""
        router.select_game(0)
        result = router.start_game()

        assert result is True
        assert router.current_game is not None
        assert len(router.current_game.target_words) == DEFAULT_WORD_COUNT

    def test_start_game_invalid_selection(self, router):
        """Test starting game with invalid selection."""
        router.selected_game_index = 99  # Invalid
        result = router.start_game()

        assert result is False
        assert router.current_game is None

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
        assert router.current_game.status == GameStatus.READY

        result = router.process_game_input("t")

        assert result is True
        assert router.current_game.status == GameStatus.ACTIVE

    def test_cancel_game(self, router):
        """Test cancelling a game."""
        router.select_game(0)
        router.start_game({"word_count": 5})

        result = router.cancel_game()

        assert result is True
        assert router.current_game is None

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
        assert len(data["target_words"]) == 5

    def test_get_game_stats_no_game(self, router):
        """Test getting stats without game."""
        stats = router.get_game_stats()

        assert stats is None

    def test_get_game_stats_with_game(self, router):
        """Test getting stats with active game."""
        router.select_game(0)
        router.start_game({"word_count": 5})
        first_word = router.current_game.target_words[0]
        router.process_game_input(first_word, is_complete=True)

        stats = router.get_game_stats()

        assert stats is not None
        assert "wpm" in stats
        assert "accuracy" in stats
        assert "elapsed_time" in stats

    def test_finish_game_no_game(self, router):
        """Test finishing game when no game active."""
        result = router.finish_game()

        assert result is None

    def test_finish_game_cancelled_not_saved(self, router, repository):
        """A cancelled game is never finished or persisted."""
        router.select_game(0)
        router.start_game({"word_count": 5})
        router.current_game.cancel()

        assert router.finish_game() is None
        assert repository.get_all() == []

    def test_return_to_main_menu(self, router):
        """Test returning to main menu."""
        router.return_to_main_menu()

        assert router.selected_game_index == 0

    def test_return_to_main_menu_cancels_active_game(self, router):
        """Test returning to menu cancels active game."""
        router.select_game(0)
        router.start_game({"word_count": 5})

        assert router.is_game_active()

        router.return_to_main_menu()

        assert not router.is_game_active()
        assert router.current_game is None

    def test_start_game_invalid_config(self, router):
        """Test starting game with invalid config."""
        router.select_game(0)
        result = router.start_game({"word_count": 500})

        assert result is False
        assert router.current_game is None

    def test_process_complete_word(self, router):
        """Test processing a complete word submission."""
        router.select_game(0)
        router.start_game({"word_count": 5})

        first_word = router.current_game.target_words[0]
        router.process_game_input(first_word, is_complete=True)

        assert router.current_game.current_word_index == 1

    def test_game_completion(self, router):
        """Test completing all words finishes the game."""
        router.select_game(0)
        router.start_game({"word_count": 5})

        for word in router.current_game.target_words:
            router.process_game_input(word, is_complete=True)

        assert router.current_game.status == GameStatus.COMPLETED

    def test_finish_game_saves_to_history(self, router, repository):
        """Test that finishing a game persists the result."""
        router.select_game(0)
        router.start_game({"word_count": 5})

        for word in router.current_game.target_words:
            router.process_game_input(word, is_complete=True)

        result = router.finish_game()
        assert result is not None
        assert result.wpm >= 0
        assert result.accuracy >= 0

        history = repository.get_all()
        assert len(history) == 1
        assert history[0].wpm == result.wpm

    def test_finish_game_first_is_new_record(self, router):
        """Test that the first completed game is always a new record."""
        router.select_game(0)
        router.start_game({"word_count": 5})

        for word in router.current_game.target_words:
            router.process_game_input(word, is_complete=True)

        router.current_game.start_time -= 60

        result = router.finish_game()
        assert result.is_new_record is True

    def test_is_game_finished(self, router):
        """Test is_game_finished() state tracking."""
        assert not router.is_game_finished()

        router.select_game(0)
        router.start_game({"word_count": 5})

        for word in router.current_game.target_words:
            router.process_game_input(word, is_complete=True)

        router.finish_game()
        assert router.is_game_finished()

    def test_restart_game_same_text(self, router):
        """Test restarting a game preserves target words."""
        router.select_game(1)
        router.start_game()
        original_words = router.current_game.target_words.copy()

        assert router.restart_game(keep_same_text=True)
        assert router.current_game is not None
        assert router.current_game.target_words == original_words
        assert router.selected_game_index == 1

    def test_restart_game_same_text_preserves_phrase(self, router):
        """Restarting with the same text keeps the phrase identity too."""
        router.select_game(1)
        router.start_game()
        original_phrase = router.current_game.phrase_text
        assert original_phrase is not None

        assert router.restart_game(keep_same_text=True)
        assert router.current_game.phrase_text == original_phrase

    def test_restart_game_new_text(self, router):
        """Test restarting generates fresh content."""
        router.select_game(0)
        router.start_game({"word_count": 5})

        assert router.restart_game()
        assert router.current_game is not None
        assert router.selected_game_index == 0


class TestGhostRecording:
    """Tests for input-snapshot recording and ghost saving."""

    @pytest.fixture
    def ghost_service(self, tmp_path):
        """Create a ghost service on a temp database."""
        repo = SqliteGhostRepository(db_path=tmp_path / "test.db")
        yield GhostService(repo)
        repo.close()

    @pytest.fixture
    def ghost_router(self, tmp_path, ghost_service):
        """Create a router with history and ghosts sharing one database.

        Ghost runs reference history rows by foreign key, so the
        production wiring (one SQLite file for both) is reproduced here.
        """
        history_repo = SqliteHistoryRepository(db_path=tmp_path / "test.db")
        yield ApplicationRouter(history_repo, ghost_service)
        history_repo.close()

    @staticmethod
    def _type_word(router, word, submit=True):
        """Feed a word character by character, then optionally submit it."""
        for i in range(1, len(word) + 1):
            router.process_game_input(word[:i], is_complete=False)
        if submit:
            router.process_game_input(word, is_complete=True)

    def test_phrase_run_records_snapshots(self, ghost_router):
        """Typing a phrase produces per-input events with submit markers."""
        ghost_router.select_game(1)
        ghost_router.start_game()
        first_word = ghost_router.current_game.target_words[0]

        self._type_word(ghost_router, first_word)

        events = ghost_router.ghost_recorder.recording
        assert len(events) == len(first_word) + 1
        assert [e.v for e in events[:-1]] == [
            first_word[: i + 1] for i in range(len(first_word))
        ]
        assert all(e.w == 0 for e in events)
        assert events[-1].s is True
        assert all(not e.s for e in events[:-1])
        # Timing is monotonic and starts at the first keystroke
        times = [e.t for e in events]
        assert times == sorted(times)
        assert times[0] == 0

    def test_random_words_run_records_nothing(self, ghost_router):
        """Non-phrase games are not recorded."""
        ghost_router.select_game(0)
        ghost_router.start_game({"word_count": 5})

        self._type_word(ghost_router, ghost_router.current_game.target_words[0])

        assert ghost_router.ghost_recorder.recording == ()

    def test_recorder_resets_on_new_game(self, ghost_router):
        """Starting a new game drops the previous run's events."""
        ghost_router.select_game(1)
        ghost_router.start_game()
        self._type_word(ghost_router, ghost_router.current_game.target_words[0])
        assert ghost_router.ghost_recorder.recording

        ghost_router.restart_game()

        assert ghost_router.ghost_recorder.recording == ()

    def test_finish_auto_saves_qualifying_ghost(self, ghost_router, ghost_service):
        """A completed phrase run is auto-saved as ghost in AUTO_BEST mode."""
        ghost_router.select_game(1)
        ghost_router.start_game()
        phrase = ghost_router.current_game.phrase_text

        for word in ghost_router.current_game.target_words:
            self._type_word(ghost_router, word)
        ghost_router.current_game.start_time -= 60

        result = ghost_router.finish_game()
        assert result is not None

        ghost = ghost_service.get_ghost_for_phrase(result.phrase_hash)
        assert ghost is not None
        assert ghost.phrase_text == phrase
        assert ghost.wpm == result.wpm
        assert ghost.recording
        assert ghost.game_history_id is not None

    def test_finish_without_ghost_service_still_works(self, router):
        """Routers without a ghost service finish games normally."""
        router.select_game(1)
        router.start_game()
        for word in router.current_game.target_words:
            self._type_word(router, word)

        assert router.finish_game() is not None


class TestGhostRaceState:
    """Tests for the active_ghost race lifecycle."""

    @pytest.fixture
    def racing_router(self, router):
        """A router with a phrase game running and a fake active ghost."""
        router.select_game(1)
        router.start_game()
        router.active_ghost = object()  # identity is all that matters here
        return router

    def test_start_game_clears_active_ghost(self, racing_router):
        """A fresh game start ends any race."""
        racing_router.start_game()
        assert racing_router.active_ghost is None

    def test_restart_same_text_keeps_ghost(self, racing_router):
        """Restarting the same phrase restarts the race too."""
        ghost = racing_router.active_ghost
        assert racing_router.restart_game(keep_same_text=True)
        assert racing_router.active_ghost is ghost

    def test_restart_new_text_ends_race(self, racing_router):
        """Moving to a new phrase ends the race."""
        assert racing_router.restart_game(keep_same_text=False)
        assert racing_router.active_ghost is None

    def test_cancel_game_ends_race(self, racing_router):
        """Cancelling the game ends the race."""
        racing_router.cancel_game()
        assert racing_router.active_ghost is None

    def test_return_to_menu_ends_race(self, racing_router):
        """Returning to the menu ends the race."""
        racing_router.return_to_main_menu()
        assert racing_router.active_ghost is None


class TestStatisticsIntegration:
    """Tests for statistics integration."""

    def test_get_all_games_empty(self, router):
        """Test getting all games with no history."""
        games = router.get_all_games()
        assert games == []

    def test_get_all_games_with_data(self, router_with_data):
        """Test getting all games with data."""
        games = router_with_data.get_all_games()
        assert len(games) == 5
