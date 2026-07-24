"""Ghost race game mode: phrase typing against a saved ghost."""

from termtypr.games.phrase_typing_game import PhraseTypingGame


class GhostRaceGame(PhraseTypingGame):
    """Phrase typing against the replay of a saved run.

    The router picks a random saved ghost when this mode starts and
    replaces the freshly drawn phrase with the ghost's phrase - games
    themselves have no repository access.
    """

    DISPLAY_NAME = "Race a Ghost"
    GAME_DESCRIPTION = "Race the ghost replays of your best phrase runs"
