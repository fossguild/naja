#!/usr/bin/env python3
"""Integration tests for scoring system with scoreboard."""

import tempfile
import pytest

from ecs.world import World
from ecs.board import Board
from ecs.systems.scoring import ScoringSystem
from ecs.components.score import Score
from game.settings import GameSettings
from game.scoreboard import Scoreboard


class TestScoringSystemIntegration:
    """Test scoring system integration with scoreboard."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.board = Board(width=20, height=20, cell_size=20)
        self.world = World(self.board)
        self.settings = GameSettings(640, 20)
        self.gamemode = "Classic Snake Game"
        self.scoreboard = Scoreboard()

        # Create a score entity
        class ScoreEntity:
            def __init__(self):
                self.score = Score(current=0, high_score=0)

            def get_type(self):
                return None

        self.score_entity = ScoreEntity()
        self.world.registry.add(self.score_entity)

    def test_scoring_system_with_scoreboard(self):
        """Test that scoring system can save scores to scoreboard."""
        scoring_system = ScoringSystem(
            scoreboard=self.scoreboard, settings=self.settings, gamemode=self.gamemode
        )

        # Simulate eating apples
        scoring_system.on_apple_eaten(self.world, 1)
        scoring_system.on_apple_eaten(self.world, 1)
        scoring_system.on_apple_eaten(self.world, 1)

        current_score = scoring_system.get_current_score(self.world)
        assert current_score == 3

        # Save score to scoreboard
        success = scoring_system.save_score_to_scoreboard(self.world)
        assert success is True

        # Verify score was saved
        sorted_scores = self.scoreboard.sorted_scores(self.settings, self.gamemode)
        assert len(sorted_scores) == 1
        assert sorted_scores[0]["value"] == 3

    def test_scoring_system_save_zero_score(self):
        """Test that zero scores are not saved."""
        scoring_system = ScoringSystem(
            scoreboard=self.scoreboard, settings=self.settings, gamemode=self.gamemode
        )

        # Don't eat any apples - score stays at 0
        success = scoring_system.save_score_to_scoreboard(self.world)

        # Should not save zero score
        assert success is False
        assert len(self.scoreboard._entries) == 0

    def test_scoring_system_without_scoreboard(self):
        """Test that scoring system works without scoreboard."""
        scoring_system = ScoringSystem(scoreboard=None, settings=self.settings)

        # Simulate eating apples
        scoring_system.on_apple_eaten(self.world, 1)
        scoring_system.on_apple_eaten(self.world, 1)

        current_score = scoring_system.get_current_score(self.world)
        assert current_score == 2

        # Should return False when no scoreboard
        success = scoring_system.save_score_to_scoreboard(self.world)
        assert success is False

    def test_scoring_system_high_score_tracking(self):
        """Test that high score is tracked across games."""
        scoring_system = ScoringSystem(
            scoreboard=self.scoreboard, settings=self.settings, gamemode=self.gamemode
        )

        # Game 1: Score 5
        for _ in range(5):
            scoring_system.on_apple_eaten(self.world, 1)

        high_score = scoring_system.get_high_score(self.world)
        assert high_score == 5

        # Reset current score (simulate game over)
        scoring_system.reset_current_score(self.world)
        assert scoring_system.get_current_score(self.world) == 0
        assert scoring_system.get_high_score(self.world) == 5  # High score preserved

        # Game 2: Score 3
        for _ in range(3):
            scoring_system.on_apple_eaten(self.world, 1)

        assert scoring_system.get_current_score(self.world) == 3
        assert scoring_system.get_high_score(self.world) == 5  # High score unchanged

        # Game 3: Score 10
        scoring_system.reset_current_score(self.world)
        for _ in range(10):
            scoring_system.on_apple_eaten(self.world, 1)

        assert scoring_system.get_current_score(self.world) == 10
        assert scoring_system.get_high_score(self.world) == 10  # High score updated

    def test_scoring_system_persistence(self):
        """Test that scores persist through save/load cycle."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Override scoreboard data directory
            self.scoreboard.data_dir = tmpdir

            scoring_system = ScoringSystem(
                scoreboard=self.scoreboard,
                settings=self.settings,
                gamemode=self.gamemode,
            )

            # Score some points and save
            for _ in range(5):
                scoring_system.on_apple_eaten(self.world, 1)

            scoring_system.save_score_to_scoreboard(self.world)

            # Load scoreboard in "new session"
            new_scoreboard = Scoreboard()
            new_scoreboard.data_dir = tmpdir
            new_scoreboard = new_scoreboard.reload()

            # Verify score was persisted
            sorted_scores = new_scoreboard.sorted_scores(self.settings, self.gamemode)
            assert len(sorted_scores) == 1
            assert sorted_scores[0]["value"] == 5

    def test_multiple_games_scoreboard_accumulation(self):
        """Test that multiple game scores accumulate in scoreboard."""
        scoring_system = ScoringSystem(
            scoreboard=self.scoreboard, settings=self.settings, gamemode=self.gamemode
        )

        # Play 3 games with different scores
        game_scores = [10, 15, 8]

        for game_score in game_scores:
            # Reset for new game
            scoring_system.reset_current_score(self.world)

            # Play game
            for _ in range(game_score):
                scoring_system.on_apple_eaten(self.world, 1)

            # Save score
            scoring_system.save_score_to_scoreboard(self.world)

        # Verify all scores are in scoreboard
        sorted_scores = self.scoreboard.sorted_scores(self.settings, self.gamemode)
        values = [entry["value"] for entry in sorted_scores]

        assert len(values) == 3
        assert sorted(values) == [8, 10, 15]

    def test_scoring_with_variable_points(self):
        """Test scoring with different point values."""
        scoring_system = ScoringSystem(
            scoreboard=self.scoreboard, settings=self.settings, gamemode=self.gamemode
        )

        # Eat apples with different point values
        scoring_system.on_apple_eaten(self.world, 1)  # Normal apple
        scoring_system.on_apple_eaten(self.world, 5)  # Bonus apple
        scoring_system.on_apple_eaten(self.world, 1)  # Normal apple

        current_score = scoring_system.get_current_score(self.world)
        assert current_score == 7

        # Save and verify
        scoring_system.save_score_to_scoreboard(self.world)
        sorted_scores = self.scoreboard.sorted_scores(self.settings, self.gamemode)
        assert sorted_scores[0]["value"] == 7


class TestScoringSystemWithDifferentSettings:
    """Test scoring system with different game settings."""

    def setup_method(self):
        """Set up test fixtures."""
        self.board = Board(width=20, height=20, cell_size=20)
        self.world = World(self.board)
        self.scoreboard = Scoreboard()
        self.gamemode = "Classic Snake Game"

        # Create a score entity
        class ScoreEntity:
            def __init__(self):
                self.score = Score(current=0, high_score=0)

            def get_type(self):
                return None

        self.score_entity = ScoreEntity()
        self.world.registry.add(self.score_entity)

    def test_separate_scoreboards_for_different_settings(self):
        """Test that different settings have separate score lists."""
        # Settings 1: Default
        settings1 = GameSettings(640, 20)
        scoring_system1 = ScoringSystem(
            scoreboard=self.scoreboard, settings=settings1, gamemode=self.gamemode
        )

        # Play with settings 1
        for _ in range(5):
            scoring_system1.on_apple_eaten(self.world, 1)
        scoring_system1.save_score_to_scoreboard(self.world)

        # Reset score
        scoring_system1.reset_current_score(self.world)

        # Settings 2: Different (electric walls off)
        settings2 = GameSettings(640, 20)
        settings2.set("electric_walls", False)
        scoring_system2 = ScoringSystem(
            scoreboard=self.scoreboard, settings=settings2, gamemode=self.gamemode
        )

        # Play with settings 2
        for _ in range(10):
            scoring_system2.on_apple_eaten(self.world, 1)
        scoring_system2.save_score_to_scoreboard(self.world)

        # Verify scores are separated
        scores1 = self.scoreboard.sorted_scores(settings1, self.gamemode)
        scores2 = self.scoreboard.sorted_scores(settings2, self.gamemode)

        assert len(scores1) == 1
        assert len(scores2) == 1
        assert scores1[0]["value"] == 5
        assert scores2[0]["value"] == 10


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
