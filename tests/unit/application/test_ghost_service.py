"""Tests for ghost save conditions and persistence coordination."""

from datetime import datetime, timezone

import pytest

from termtypr.application.ghost_service import GhostService
from termtypr.config import user_preferences
from termtypr.domain.models.game_result import GameResult
from termtypr.domain.models.ghost_run import RecordingEvent
from termtypr.domain.models.user_preferences import GhostSaveMode, UserPreferences
from termtypr.infrastructure.persistence.sqlite_ghost_repository import (
    SqliteGhostRepository,
)
from termtypr.infrastructure.persistence.sqlite_history_repository import (
    SqliteHistoryRepository,
)

RECORDING = (
    RecordingEvent(t=0, w=0, v="h"),
    RecordingEvent(t=200, w=0, v="hi", s=True),
)


def make_result(
    wpm: float = 70.0,
    accuracy: float = 95.0,
    phrase_text: str | None = "hi there",
) -> GameResult:
    """Build a completed phrase result for tests."""
    return GameResult(
        wpm=wpm,
        accuracy=accuracy,
        duration=10.0,
        game_type="Phrase Typing",
        timestamp=datetime.now(tz=timezone.utc),
        phrase_text=phrase_text,
    )


@pytest.fixture(autouse=True)
def _reset_ghost_preferences():
    """Give every test deterministic ghost preferences, restored afterwards."""
    defaults = UserPreferences()
    saved = {
        "ghost_save_mode": user_preferences.ghost_save_mode,
        "ghost_wpm_threshold": user_preferences.ghost_wpm_threshold,
        "ghost_min_accuracy": user_preferences.ghost_min_accuracy,
        "max_ghosts_total": user_preferences.max_ghosts_total,
    }
    user_preferences.ghost_save_mode = defaults.ghost_save_mode
    user_preferences.ghost_wpm_threshold = defaults.ghost_wpm_threshold
    user_preferences.ghost_min_accuracy = defaults.ghost_min_accuracy
    user_preferences.max_ghosts_total = defaults.max_ghosts_total
    yield
    for key, value in saved.items():
        setattr(user_preferences, key, value)


@pytest.fixture
def repository(tmp_path):
    """Create a ghost repository backed by a fresh temp database."""
    repo = SqliteGhostRepository(db_path=tmp_path / "test.db")
    yield repo
    repo.close()


@pytest.fixture
def service(repository):
    """Create a ghost service on the temp repository."""
    return GhostService(repository)


class TestQualifies:
    """Tests for the quality floor shared by all save paths."""

    def test_good_phrase_run_qualifies(self, service):
        """A phrase run with real WPM and accuracy qualifies."""
        assert service.qualifies(make_result()) is True

    def test_non_phrase_run_never_qualifies(self, service):
        """Runs without a phrase (random words) never qualify."""
        assert service.qualifies(make_result(phrase_text=None)) is False

    def test_zero_wpm_does_not_qualify(self, service):
        """A run with no meaningful WPM does not qualify."""
        assert service.qualifies(make_result(wpm=0.0)) is False

    def test_low_accuracy_does_not_qualify(self, service):
        """Accuracy below the configured floor disqualifies a run."""
        user_preferences.ghost_min_accuracy = 85.0
        assert service.qualifies(make_result(accuracy=80.0)) is False


class TestShouldAutoSave:
    """Tests for automatic save decisions per mode."""

    def test_never_mode(self, service):
        """NEVER mode saves nothing."""
        user_preferences.ghost_save_mode = GhostSaveMode.NEVER
        assert service.should_auto_save(make_result()) is False

    def test_ask_mode_does_not_auto_save(self, service):
        """ALWAYS_ASK defers to the user instead of auto-saving."""
        user_preferences.ghost_save_mode = GhostSaveMode.ALWAYS_ASK
        assert service.should_auto_save(make_result()) is False
        assert service.should_prompt(make_result()) is True

    def test_auto_best_saves_first_run(self, service):
        """AUTO_BEST saves a phrase's first qualifying run."""
        user_preferences.ghost_save_mode = GhostSaveMode.AUTO_BEST
        assert service.should_auto_save(make_result()) is True

    def test_auto_best_replaces_only_better_runs(self, service):
        """AUTO_BEST keeps the phrase's best run by wpm*accuracy."""
        user_preferences.ghost_save_mode = GhostSaveMode.AUTO_BEST
        service.save_ghost(make_result(wpm=70.0, accuracy=95.0), RECORDING)

        assert service.should_auto_save(make_result(wpm=60.0, accuracy=95.0)) is False
        assert service.should_auto_save(make_result(wpm=80.0, accuracy=95.0)) is True

    def test_auto_threshold_respects_threshold(self, service):
        """AUTO_THRESHOLD only saves runs at or above the WPM threshold."""
        user_preferences.ghost_save_mode = GhostSaveMode.AUTO_THRESHOLD
        user_preferences.ghost_wpm_threshold = 60.0

        assert service.should_auto_save(make_result(wpm=59.9)) is False
        assert service.should_auto_save(make_result(wpm=60.0)) is True

    def test_prompt_only_in_ask_mode(self, service):
        """should_prompt is specific to ALWAYS_ASK."""
        user_preferences.ghost_save_mode = GhostSaveMode.AUTO_BEST
        assert service.should_prompt(make_result()) is False


class TestSaveGhost:
    """Tests for persisting ghosts."""

    def test_save_ghost_persists_run(self, service, repository, tmp_path):
        """save_ghost stores the run with its recording and history link."""
        history_repo = SqliteHistoryRepository(db_path=tmp_path / "test.db")
        result = make_result()
        history_id = history_repo.save(result)

        ghost = service.save_ghost(result, RECORDING, history_id=history_id)

        assert ghost.id is not None
        stored = repository.get_by_phrase_hash(result.phrase_hash)
        assert stored.wpm == result.wpm
        assert stored.recording == RECORDING
        assert stored.game_history_id == history_id
        history_repo.close()

    def test_save_ghost_rejects_non_phrase_runs(self, service):
        """Runs without a phrase cannot become ghosts."""
        with pytest.raises(ValueError, match="phrase"):
            service.save_ghost(make_result(phrase_text=None), RECORDING)

    def test_save_ghost_enforces_global_cap(self, service, repository):
        """Saving prunes the worst runs beyond max_ghosts_total."""
        user_preferences.max_ghosts_total = 1

        service.save_ghost(make_result(wpm=50.0, phrase_text="slow one"), RECORDING)
        service.save_ghost(make_result(wpm=90.0, phrase_text="fast one"), RECORDING)

        ghosts = repository.get_all()
        assert [g.phrase_text for g in ghosts] == ["fast one"]
