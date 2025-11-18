#!/usr/bin/env python3
"""Tests for game over scene display functionality."""

from datetime import datetime
from unittest.mock import Mock, patch

from game.scenes.game_over import GameOverScene
from game.scoreboard import Scoreboard, MAX_SCOREBOARD_ENTRIES
from game.settings import GameSettings
from ecs.world import World
from ecs.board import Board


class TestGameOverSceneDisplay:
    """Test game over scene display functionality."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.board = Board(width=20, height=20, cell_size=20)
        self.world = World(self.board)
        self.settings = GameSettings(640, 20)
        self.scoreboard = Scoreboard()

        # Mock pygame adapter and renderer
        self.pygame_adapter = Mock()
        self.renderer = Mock()
        self.assets = Mock()

        # Set up default window dimensions
        self.width = 800
        self.height = 600

    def create_game_state_entity(self, final_score: int):
        """Helper to create a game state entity with a final score."""

        class GameStateComponent:
            def __init__(self, score):
                self.final_score = score

        class GameStateEntity:
            def __init__(self, score):
                self.game_state = GameStateComponent(score)

        entity = GameStateEntity(final_score)
        self.world.registry.add(entity)
        return entity

    def test_new_high_score_detection_empty_scoreboard(self):
        """Test that new high score is detected when scoreboard is empty."""
        scene = GameOverScene(
            self.pygame_adapter,
            self.renderer,
            self.width,
            self.height,
            self.assets,
            settings=self.settings,
            scoreboard=self.scoreboard,
            world=self.world,
        )

        # Add a game state with a score
        self.create_game_state_entity(100)

        # Add score to scoreboard
        self.scoreboard.add_entry(self.settings, 100)

        # Enter the scene
        with patch("pygame.mixer.music.load"), patch("pygame.mixer.music.play"):
            scene.on_enter()

        # Should be detected as new high score
        assert scene._is_new_high_score is True
        assert scene._current_score == 100

    def test_new_high_score_detection_beats_existing(self):
        """Test that new high score is detected when it beats existing scores."""
        # Add some existing scores
        self.scoreboard.add_entry(self.settings, 50)
        self.scoreboard.add_entry(self.settings, 75)
        self.scoreboard.add_entry(self.settings, 90)

        scene = GameOverScene(
            self.pygame_adapter,
            self.renderer,
            self.width,
            self.height,
            self.assets,
            settings=self.settings,
            scoreboard=self.scoreboard,
            world=self.world,
        )

        # Add a game state with a score that beats existing high score
        self.create_game_state_entity(150)

        # Add the new score to scoreboard
        self.scoreboard.add_entry(self.settings, 150)

        # Enter the scene
        with patch("pygame.mixer.music.load"), patch("pygame.mixer.music.play"):
            scene.on_enter()

        # Should be detected as new high score
        assert scene._is_new_high_score is True
        assert scene._current_score == 150

    def test_not_high_score_when_lower(self):
        """Test that score is not marked as high score when it's lower than existing."""
        # Add some existing scores
        self.scoreboard.add_entry(self.settings, 100)
        self.scoreboard.add_entry(self.settings, 150)
        self.scoreboard.add_entry(self.settings, 200)

        scene = GameOverScene(
            self.pygame_adapter,
            self.renderer,
            self.width,
            self.height,
            self.assets,
            settings=self.settings,
            scoreboard=self.scoreboard,
            world=self.world,
        )

        # Add a game state with a score lower than high score
        self.create_game_state_entity(75)

        # Add the new score to scoreboard
        self.scoreboard.add_entry(self.settings, 75)

        # Enter the scene
        with patch("pygame.mixer.music.load"), patch("pygame.mixer.music.play"):
            scene.on_enter()

        # Should NOT be detected as new high score
        assert scene._is_new_high_score is False
        assert scene._current_score == 75

    def test_timestamp_capture_for_new_score(self):
        """Test that timestamp is captured for the new score."""
        # Add the score to scoreboard first
        self.scoreboard.add_entry(self.settings, 100)

        scene = GameOverScene(
            self.pygame_adapter,
            self.renderer,
            self.width,
            self.height,
            self.assets,
            settings=self.settings,
            scoreboard=self.scoreboard,
            world=self.world,
        )

        # Add a game state with matching score
        self.create_game_state_entity(100)

        # Enter the scene
        with patch("pygame.mixer.music.load"), patch("pygame.mixer.music.play"):
            scene.on_enter()

        # Timestamp should be captured
        assert scene._new_score_timestamp is not None
        assert isinstance(scene._new_score_timestamp, datetime)

    def test_zero_score_not_high_score(self):
        """Test that zero score is not marked as high score."""
        scene = GameOverScene(
            self.pygame_adapter,
            self.renderer,
            self.width,
            self.height,
            self.assets,
            settings=self.settings,
            scoreboard=self.scoreboard,
            world=self.world,
        )

        # Add a game state with zero score
        self.create_game_state_entity(0)

        # Add zero score to scoreboard
        self.scoreboard.add_entry(self.settings, 0)

        # Enter the scene
        with patch("pygame.mixer.music.load"), patch("pygame.mixer.music.play"):
            scene.on_enter()

        # Should NOT be detected as new high score
        assert scene._is_new_high_score is False

    def test_zero_score_no_highlighting_in_list(self):
        """Test that zero score doesn't get highlighted even if it matches timestamp."""
        # Add some existing scores
        self.scoreboard.add_entry(self.settings, 50)
        self.scoreboard.add_entry(self.settings, 100)

        # Add zero score
        self.scoreboard.add_entry(self.settings, 0)

        scene = GameOverScene(
            self.pygame_adapter,
            self.renderer,
            self.width,
            self.height,
            self.assets,
            settings=self.settings,
            scoreboard=self.scoreboard,
            world=self.world,
        )

        # Set current score to 0
        self.create_game_state_entity(0)

        # Enter the scene
        with patch("pygame.mixer.music.load"), patch("pygame.mixer.music.play"):
            scene.on_enter()

        # Even though we have a timestamp match, zero score should not be highlighted
        # This is verified by checking that _is_new_high_score is False
        assert scene._is_new_high_score is False
        assert scene._current_score == 0

    def test_top_5_scores_display(self):
        """Test that top scores are properly prepared for display."""
        # Add more than MAX_SCOREBOARD_ENTRIES scores
        for score in [10, 20, 30, 40, 50, 60, 70, 80]:
            self.scoreboard.add_entry(self.settings, score)

        # Get sorted scores
        sorted_scores = self.scoreboard.sorted_scores(self.settings)
        # Take top entries (highest scores)
        top_scores = sorted_scores[:MAX_SCOREBOARD_ENTRIES]

        # Should have exactly MAX_SCOREBOARD_ENTRIES scores
        assert len(top_scores) == MAX_SCOREBOARD_ENTRIES

        # Should be in descending order (highest first)
        assert top_scores[0]["value"] == 80
        assert top_scores[1]["value"] == 70
        assert top_scores[2]["value"] == 60
        assert top_scores[3]["value"] == 50
        assert top_scores[4]["value"] == 40

    def test_timestamp_formatting_in_scores(self):
        """Test that timestamps are properly included in score entries."""
        # Add score with known timestamp
        self.scoreboard.add_entry(self.settings, 100)

        sorted_scores = self.scoreboard.sorted_scores(self.settings)

        assert len(sorted_scores) > 0
        assert "timestamp" in sorted_scores[0]
        assert isinstance(sorted_scores[0]["timestamp"], datetime)

    def test_scene_without_scoreboard(self):
        """Test that scene handles missing scoreboard gracefully."""
        scene = GameOverScene(
            self.pygame_adapter,
            self.renderer,
            self.width,
            self.height,
            self.assets,
            settings=None,
            scoreboard=None,
            world=self.world,
        )

        # Add a game state
        self.create_game_state_entity(100)

        # Should not crash
        with patch("pygame.mixer.music.load"), patch("pygame.mixer.music.play"):
            scene.on_enter()

        assert scene._is_new_high_score is False
        assert scene._new_score_timestamp is None

    def test_equal_score_to_high_score(self):
        """Test behavior when new score equals existing high score."""
        # Add an existing high score
        self.scoreboard.add_entry(self.settings, 100)

        scene = GameOverScene(
            self.pygame_adapter,
            self.renderer,
            self.width,
            self.height,
            self.assets,
            settings=self.settings,
            scoreboard=self.scoreboard,
            world=self.world,
        )

        # Add a game state with equal score
        self.create_game_state_entity(100)

        # Add the new score to scoreboard
        self.scoreboard.add_entry(self.settings, 100)

        # Enter the scene
        with patch("pygame.mixer.music.load"), patch("pygame.mixer.music.play"):
            scene.on_enter()

        # Should not be marked as high score (tied for highest and oldest)
        assert scene._is_new_high_score is False

    def test_equal_score_but_not_most_recent(self):
        """Test that tying high score but not being most recent doesn't show as new high."""
        # Add two scores at 100
        self.scoreboard.add_entry(self.settings, 100)
        self.scoreboard.add_entry(self.settings, 100)

        scene = GameOverScene(
            self.pygame_adapter,
            self.renderer,
            self.width,
            self.height,
            self.assets,
            settings=self.settings,
            scoreboard=self.scoreboard,
            world=self.world,
        )

        # Set current score to match but use a non-most-recent timestamp
        self.create_game_state_entity(100)

        # Get the sorted scores - first entry has the most recent timestamp for value 100
        sorted_scores = self.scoreboard.sorted_scores(self.settings)
        scene._current_score = 100
        # Use the second timestamp (older one, not the most recent)
        scene._new_score_timestamp = sorted_scores[1]["timestamp"]

        # Call the high score check logic manually (simulating on_enter)
        if scene._scoreboard and scene._settings and scene._current_score > 0:
            sorted_scores = scene._scoreboard.sorted_scores(scene._settings)
            if sorted_scores:
                highest_score = sorted_scores[0][
                    "value"
                ]  # First entry has highest score
                if scene._current_score == highest_score:
                    # Check if our timestamp matches the first (most recent) entry
                    if scene._new_score_timestamp == sorted_scores[0]["timestamp"]:
                        scene._is_new_high_score = True

        # Should NOT be marked as new high score (not the most recent)
        assert scene._is_new_high_score is False


class TestScoreHighlighting:
    """Test score highlighting functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.board = Board(width=20, height=20, cell_size=20)
        self.world = World(self.board)
        self.settings = GameSettings(640, 20)
        self.scoreboard = Scoreboard()

        self.pygame_adapter = Mock()
        self.renderer = Mock()
        self.assets = Mock()
        self.width = 800
        self.height = 600

    def test_timestamp_matching_identifies_new_score(self):
        """Test that timestamp matching correctly identifies the new score in list."""
        # Manually create entries with specific timestamps
        self.scoreboard.add_entry(self.settings, 50)
        self.scoreboard.add_entry(self.settings, 75)

        # Add the "new" score
        self.scoreboard.add_entry(self.settings, 90)

        scene = GameOverScene(
            self.pygame_adapter,
            self.renderer,
            self.width,
            self.height,
            self.assets,
            settings=self.settings,
            scoreboard=self.scoreboard,
            world=self.world,
        )

        # Create game state entity
        class GameStateComponent:
            def __init__(self):
                self.final_score = 90

        class GameStateEntity:
            def __init__(self):
                self.game_state = GameStateComponent()

        entity = GameStateEntity()
        self.world.registry.add(entity)

        # Enter scene
        with patch("pygame.mixer.music.load"), patch("pygame.mixer.music.play"):
            scene.on_enter()

        # Should capture the timestamp of the most recent score with value 90
        assert scene._new_score_timestamp is not None

        # The timestamp should match the latest 90 score
        sorted_scores = self.scoreboard.sorted_scores(self.settings)
        matching_scores = [s for s in sorted_scores if s["value"] == 90]
        assert len(matching_scores) > 0
        assert scene._new_score_timestamp == matching_scores[-1]["timestamp"]


class TestGameOverSceneLayout:
    """Test layout and spacing improvements."""

    def setup_method(self):
        """Set up test fixtures."""
        self.board = Board(width=20, height=20, cell_size=20)
        self.world = World(self.board)
        self.settings = GameSettings(640, 20)
        self.scoreboard = Scoreboard()

        self.pygame_adapter = Mock()
        self.renderer = Mock()
        self.assets = Mock()
        self.width = 800
        self.height = 600

    def test_scene_initialization_with_all_components(self):
        """Test that scene initializes with all required components."""
        scene = GameOverScene(
            self.pygame_adapter,
            self.renderer,
            self.width,
            self.height,
            self.assets,
            death_reason="Collision",
            settings=self.settings,
            scoreboard=self.scoreboard,
            world=self.world,
        )

        assert scene._settings == self.settings
        assert scene._scoreboard == self.scoreboard
        assert scene._world == self.world
        assert scene._current_score == 0
        assert scene._is_new_high_score is False
        assert scene._new_score_timestamp is None

    def test_fewer_than_5_scores_handled(self):
        """Test that display handles fewer scores than max correctly."""
        # Add only 3 scores
        self.scoreboard.add_entry(self.settings, 10)
        self.scoreboard.add_entry(self.settings, 20)
        self.scoreboard.add_entry(self.settings, 30)

        sorted_scores = self.scoreboard.sorted_scores(self.settings)
        # Take top entries (highest scores)
        top_scores = (
            sorted_scores[:MAX_SCOREBOARD_ENTRIES]
            if len(sorted_scores) >= MAX_SCOREBOARD_ENTRIES
            else sorted_scores
        )

        # Should have exactly 3 scores
        assert len(top_scores) == 3
        # Should be in descending order (highest first)
        assert top_scores[0]["value"] == 30
        assert top_scores[1]["value"] == 20
        assert top_scores[2]["value"] == 10
