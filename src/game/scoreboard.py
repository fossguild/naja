"""Scoreboard management for persistent high score tracking.

This module provides functionality to track, persist, and retrieve game scores
across multiple sessions. Scores are separated by game settings configurations,
allowing different scoreboards for different difficulty levels or game modes.

The scoreboard uses a SHA256 hash of relevant game settings to create separate
leaderboards for each unique configuration. Scores are stored in the user's
data directory using platformdirs for cross-platform compatibility.
"""

import os
import json
from typing import Any, TypedDict
from game.settings import GameSettings
from game.game_modes_registry import GameModeType
from game.constants import USER_DATA_DIR
from datetime import datetime
from hashlib import sha256

# Filename for the scoreboard persistence file
SCOREBOARD_FILE_NAME = "scoreboard.json"

# Maximum number of top scores to display in the game over screen
# Change this value to show more or fewer scores in the leaderboard
MAX_SCOREBOARD_ENTRIES = 5

# Type definition for a single score entry
# Contains the score value and the timestamp when it was achieved
ScoreboardEntry = TypedDict("ScoreboardEntry", {"value": int, "timestamp": datetime})

# Type definition for a scoreboard listing per settings configuration and gamemode
# Each unique game configuration has its own listing with associated scores
ScoreboardListing = TypedDict(
    "ScoreboardListing",
    {
        "gamemode": GameModeType,
        "settings": dict[str, Any],
        "hash": str,
        "scores": list[ScoreboardEntry],
    },
)


class Scoreboard:
    """Manages game score persistence and retrieval.

    The Scoreboard maintains separate leaderboards for each unique game
    configuration. It uses SHA256 hashes of game settings to identify
    different configurations and stores all scores with timestamps.

    Scores are persisted to disk in JSON format in the user's data directory,
    allowing them to persist across game sessions.

    Attributes:
        _entries: Dictionary mapping settings hashes to their scoreboard listings.
                 Each listing contains the settings, hash, and list of scores.
        data_dir: Path to the directory where scoreboard data is stored.
                 Set automatically to the platform-specific user data directory.

    Example:
        >>> scoreboard = Scoreboard()
        >>> settings = GameSettings(640, 20)
        >>> scoreboard.add_entry(settings, 100)
        >>> scores = scoreboard.sorted_scores(settings)
        >>> scoreboard.save()
    """

    _entries: dict[str, ScoreboardListing]

    def __init__(self):
        """Initialize an empty scoreboard.

        Creates a new scoreboard with no entries. To load existing scores
        from disk, use the `load()` static method or call `reload()`.
        """
        self._entries = {}

    def _hash(self, settings: GameSettings, gamemode: GameModeType) -> str:
        settings_str = json.dumps(settings.scoreboard_settings())
        gamemode_str = json.dumps(gamemode)
        return sha256((settings_str + gamemode_str).encode()).hexdigest()

    def add_entry(
        self, settings: GameSettings, gamemode: GameModeType, score: int
    ) -> None:
        """Add a new score entry for the given settings configuration.

        If this is the first score for these settings, creates a new
        scoreboard listing. The score is tagged with the current timestamp.

        Args:
            settings: The game settings under which the score was achieved.
                     Used to determine which scoreboard listing to add to.
            gamemode: The game mode under which the score was achieved.
            score: The score value to add (typically the final game score).

        Note:
            This method does not persist the score to disk. Call `save()`
            after adding entries to persist them.
        """
        listing_hash = self._hash(settings, gamemode)

        if listing_hash not in self._entries:
            self._entries[listing_hash] = {
                "gamemode": gamemode,
                "settings": settings.scoreboard_settings(),
                "hash": listing_hash,
                "scores": [],
            }

        entry: ScoreboardEntry = {"value": score, "timestamp": datetime.now()}
        self._entries[listing_hash]["scores"].append(entry)

    def all_entries(self) -> list[ScoreboardListing]:
        """Get all scoreboard listings across all settings configurations.

        Returns:
            A list of all scoreboard listings, each containing settings,
            hash, and associated scores. Useful for displaying scoreboards
            for multiple configurations.
        """
        return list(self._entries.values())

    def sorted_scores(
        self, settings: GameSettings, gamemode: GameModeType
    ) -> list[ScoreboardEntry]:
        """Get scores for specific settings, sorted by value and timestamp.

        Scores are sorted in descending order by value (highest first).
        For scores with the same value, newer scores appear first.

        Args:
            settings: The game settings configuration to retrieve scores for.
            gamemode: The game mode to retrieve scores for.

        Returns:
            A list of score entries sorted by (-value, -timestamp).
            Returns an empty list if no scores exist for the given settings.

        Note:
            The sorting key uses negative timestamp to ensure that when
            multiple scores have the same value, the most recent one appears
            first in the sorted list.
        """
        listing_hash = self._hash(settings, gamemode)
        if listing_hash not in self._entries:
            return []

        return list(
            sorted(
                self._entries[listing_hash]["scores"],
                key=lambda x: (-x["value"], x["timestamp"].timestamp()),
            )
        )

    def clear(self) -> None:
        """Remove all scoreboard entries from memory.

        This clears all scores for all settings configurations.
        To persist this change, call `save()` after clearing.

        Warning:
            This does not automatically delete the saved file. Call `save()`
            after `clear()` to remove scores from disk as well.
        """
        self._entries = {}

    def save(self) -> None:
        """Persist the current scoreboard to disk.

        Saves all scoreboard entries to a JSON file in the user's data
        directory. The directory is created if it doesn't exist.

        The file location is platform-specific:
        - Linux: ~/.local/share/naja/
        - macOS: ~/Library/Application Support/naja/
        - Windows: %APPDATA%/fossguild/naja/

        Raises:
            OSError: If the directory cannot be created or file cannot be written.

        Note:
            Datetime objects are converted to ISO format strings for JSON
            serialization. They are converted back to datetime objects when
            loading with `reload()`.
        """

        if not hasattr(self, "data_dir"):
            self.data_dir = USER_DATA_DIR
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
        with open(os.path.join(self.data_dir, SCOREBOARD_FILE_NAME), "w") as f:
            json.dump(self._entries, f, default=str)
            print("Scoreboard saved to file.")
        pass

    def reload(self) -> "Scoreboard":
        """Load scoreboard data from disk.

        Reads the scoreboard file from the user's data directory and
        replaces the current in-memory entries with the loaded data.

        If the data directory doesn't exist, it will be created.
        If no scoreboard file exists, the scoreboard remains empty.

        Returns:
            Self, allowing for method chaining.

        Raises:
            PermissionError: If the data directory is not writable.
            json.JSONDecodeError: If the scoreboard file is corrupted.

        Note:
            Timestamp strings in the JSON file are automatically converted
            back to datetime objects for in-memory use.
        """

        if not hasattr(self, "data_dir") or self.data_dir is None:
            self.data_dir = USER_DATA_DIR

        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
        if not os.access(self.data_dir, os.W_OK):
            raise PermissionError(f"Cannot write to data directory: {self.data_dir}")
        if not os.path.exists(os.path.join(self.data_dir, SCOREBOARD_FILE_NAME)):
            print("No existing scoreboard found, initializing empty one.")
            return self
        else:
            with open(os.path.join(self.data_dir, SCOREBOARD_FILE_NAME), "r") as f:
                data = json.load(f)
                # Convert timestamp strings back to datetime objects
                for listing_hash, listing in data.items():
                    for score_entry in listing.get("scores", []):
                        if "timestamp" in score_entry and isinstance(
                            score_entry["timestamp"], str
                        ):
                            score_entry["timestamp"] = datetime.fromisoformat(
                                score_entry["timestamp"]
                            )
                self._entries = data
                print("Loaded scoreboard from file.")

        return self

    @staticmethod
    def load() -> "Scoreboard":
        """Create a new Scoreboard instance and load data from disk.

        This is a convenience method that combines instantiation and loading.
        Equivalent to calling `Scoreboard().reload()`.

        Returns:
            A new Scoreboard instance with data loaded from disk.

        Example:
            >>> scoreboard = Scoreboard.load()
            >>> scores = scoreboard.sorted_scores(settings)
        """
        return Scoreboard().reload()
