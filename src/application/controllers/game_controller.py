"""Game controller for managing game lifecycle and state."""

from typing import Any, Optional

from src.config import SETTINGS
from src.domain.models.game_result import GameResult
from src.domain.models.game_state import GameState, GameStatus
from src.domain.repositories.history_repository import HistoryRepository
from src.games.base_game import BaseGame


class GameController:
    """Controller for managing game lifecycle and coordination.

    This controller acts as an intermediary between the UI layer and the game logic,
    handling:
      - Game initialization and configuration
      - State management and transitions
      - Result calculation and persistence
      - Integration with history repository
    """

    def __init__(self, history_repository: HistoryRepository):
        """Initialize the game controller.

        Args:
            history_repository: Repository for persisting game results
        """
        self.history_repository = history_repository
        self.current_game: Optional[BaseGame] = None
        self.game_state: Optional[GameState] = None

    def start_game(
        self, game_instance: BaseGame, config: Optional[dict[str, Any]] = None
    ) -> bool:
        """Start a new game with the given configuration.

        Args:
            game_instance: Instance of the game to start
            config: Optional configuration dictionary

        Returns:
            True if game started successfully, False otherwise
        """
        # Apply default configuration if not provided
        if config is None:
            config = {}

        # Apply defaults from settings
        if "word_count" not in config:
            config["word_count"] = SETTINGS.game.default_word_count

        # Initialize the game
        if not game_instance.initialize(**config):
            return False

        # Start the game
        if not game_instance.start():
            return False

        # Set as current game and create initial state
        self.current_game = game_instance
        self.game_state = GameState.create_ready(
            target_words=game_instance.target_words,
        )

        return True

    def process_input(
        self, input_text: str, is_complete: bool = False
    ) -> dict[str, Any]:
        """Process user input during the game.

        Args:
            input_text: The text input from the user
            is_complete: Whether this is a complete word submission

        Returns:
            Dictionary with processing result and updated state
        """
        if not self.current_game or not self.game_state:
            return {"status": "error", "message": "No active game"}

        # Process input through the game
        result = self.current_game.process_input(input_text, is_complete)

        # Update game state based on game's internal state
        if self.current_game.status == GameStatus.ACTIVE:
            if not self.game_state.is_active:
                # Transition to active on first input
                self.game_state = self.game_state.transition_to(GameStatus.ACTIVE)

            # Update state with current progress
            self.game_state = self.game_state.with_updates(
                current_word_index=self.current_game.current_word_index,
                typed_words=self.current_game.typed_words.copy(),
                current_input=self.current_game.current_input,
            )

        elif self.current_game.status == GameStatus.COMPLETED:
            # Transition to completed
            if self.game_state.status.can_transition_to(GameStatus.COMPLETED):
                self.game_state = self.game_state.transition_to(GameStatus.COMPLETED)

        return result

    def get_current_stats(self) -> dict[str, Any]:
        """Get current game statistics.

        Returns:
            Dictionary with current statistics
        """
        if not self.current_game:
            return {
                "wpm": 0.0,
                "accuracy": 100.0,
                "elapsed_time": 0.0,
                "characters_typed": 0,
            }

        return self.current_game.get_current_stats()

    def get_display_data(self) -> dict[str, Any]:
        """Get data for UI display.

        Returns:
            Dictionary with display data including game state
        """
        if not self.current_game or not self.game_state:
            return {}

        # Get base display data from game
        display_data = self.current_game.get_display_data()

        # Enhance with state information
        display_data.update(
            {
                "status": self.game_state.status.value,
                "words_remaining": self.game_state.words_remaining,
                "completion_percentage": self.game_state.completion_percentage,
            }
        )

        return display_data

    def finish_game(self) -> GameResult:
        """Finish the current game and return results.

        Returns:
            GameResult object with final statistics

        Raises:
            RuntimeError: If no active game to finish
        """
        if not self.current_game:
            raise RuntimeError("No active game to finish")

        # Get final result from game
        result = self.current_game.finish()

        # Check if this is a new record
        best_record = self.history_repository.get_best()
        is_new_record = best_record is None or result.wpm > best_record.wpm
        previous_best = best_record.wpm if best_record else None

        # Create enhanced result with record information
        enhanced_result = GameResult(
            wpm=result.wpm,
            accuracy=result.accuracy,
            duration=result.duration,
            game_type=result.game_type,
            timestamp=result.timestamp,
            total_characters=result.total_characters,
            correct_characters=result.correct_characters,
            error_count=result.error_count,
            is_new_record=is_new_record,
            previous_best=previous_best,
        )

        # Save to history repository
        self.history_repository.save(enhanced_result)

        # Update state to completed
        if self.game_state and self.game_state.status.can_transition_to(
            GameStatus.COMPLETED
        ):
            self.game_state = self.game_state.transition_to(GameStatus.COMPLETED)

        return enhanced_result

    def cancel_game(self) -> None:
        """Cancel the current game without saving results."""
        if self.current_game:
            self.current_game.cancel()

        if self.game_state and self.game_state.status.can_transition_to(
            GameStatus.CANCELLED
        ):
            self.game_state = self.game_state.transition_to(GameStatus.CANCELLED)

        self.current_game = None
        self.game_state = None

    def reset(self) -> None:
        """Reset the controller, clearing current game and state."""
        if self.current_game:
            self.current_game.reset()

        self.current_game = None
        self.game_state = None

    def is_game_active(self) -> bool:
        """Check if there is an active game.

        Returns:
            True if a game is currently active
        """
        return (
            self.current_game is not None
            and self.game_state is not None
            and self.game_state.is_active
        )

    def is_game_finished(self) -> bool:
        """Check if the current game is finished.

        Returns:
            True if the game is completed or cancelled
        """
        return self.game_state is not None and self.game_state.is_finished

    def get_game_state(self) -> Optional[GameState]:
        """Get the current game state.

        Returns:
            Current GameState or None if no active game
        """
        return self.game_state

    def get_elapsed_time(self) -> float:
        """Get elapsed time since game started.

        Returns:
            Elapsed time in seconds
        """
        if not self.current_game:
            return 0.0

        return self.current_game.get_elapsed_time()
