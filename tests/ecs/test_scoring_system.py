#!/usr/bin/env python3
#
#   Copyright (c) 2023, Monaco F. J. <monaco@usp.br>
#
#   This file is part of Naja.
#
#   Naja is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""Scoring system tests."""

import pytest
from dataclasses import dataclass

from ecs.world import World
from ecs.board import Board
from ecs.systems.scoring import ScoringSystem


@dataclass
class ScoreEntity:
    """Simple score entity for testing."""

    current: int = 0
    high_score: int = 0


@pytest.fixture
def board():
    """Create a standard board for testing."""
    return Board(width=10, height=10, cell_size=30)


@pytest.fixture
def world(board):
    """Create a world with board."""
    return World(board)


@pytest.fixture
def scoring_system():
    """Create a ScoringSystem."""
    return ScoringSystem()


@pytest.fixture
def world_with_score(world):
    """Create a world with a score entity."""
    score_entity = ScoreEntity(current=0, high_score=0)
    world.registry.add(score_entity)
    return world


class TestScoringSystemInitialization:
    """Test ScoringSystem initialization."""

    def test_system_created_successfully(self):
        """Test that ScoringSystem can be initialized."""
        system = ScoringSystem()
        assert system is not None

    def test_system_with_callback(self):
        """Test ScoringSystem with callback."""
        callback_called = []

        def score_callback(current, high):
            callback_called.append((current, high))

        system = ScoringSystem(score_callback=score_callback)
        assert system._score_callback is not None


class TestAppleEatenScoring:
    """Test score updates when apples are eaten."""

    def test_on_apple_eaten_increases_score(self, world_with_score, scoring_system):
        """Test that eating apple increases score."""
        scoring_system.on_apple_eaten(world_with_score, points=10)

        current_score = scoring_system.get_current_score(world_with_score)
        assert current_score == 10

    def test_on_apple_eaten_multiple_times(self, world_with_score, scoring_system):
        """Test eating multiple apples accumulates score."""
        scoring_system.on_apple_eaten(world_with_score, points=10)
        scoring_system.on_apple_eaten(world_with_score, points=10)
        scoring_system.on_apple_eaten(world_with_score, points=10)

        current_score = scoring_system.get_current_score(world_with_score)
        assert current_score == 30

    def test_on_apple_eaten_different_points(self, world_with_score, scoring_system):
        """Test apples with different point values."""
        scoring_system.on_apple_eaten(world_with_score, points=5)
        scoring_system.on_apple_eaten(world_with_score, points=15)
        scoring_system.on_apple_eaten(world_with_score, points=20)

        current_score = scoring_system.get_current_score(world_with_score)
        assert current_score == 40

    def test_on_apple_eaten_without_score_entity(self, world, scoring_system):
        """Test eating apple when no score entity exists."""
        # should not crash
        scoring_system.on_apple_eaten(world, points=10)

        # score should remain 0
        current_score = scoring_system.get_current_score(world)
        assert current_score == 0


class TestHighScoreTracking:
    """Test high score tracking."""

    def test_high_score_updates_when_exceeded(self, world_with_score, scoring_system):
        """Test that high score updates when current exceeds it."""
        scoring_system.on_apple_eaten(world_with_score, points=50)

        high_score = scoring_system.get_high_score(world_with_score)
        assert high_score == 50

    def test_high_score_does_not_decrease(self, world_with_score, scoring_system):
        """Test that high score is preserved even if current score resets."""
        # set a high score
        scoring_system.on_apple_eaten(world_with_score, points=100)
        assert scoring_system.get_high_score(world_with_score) == 100

        # reset current score
        scoring_system.reset_current_score(world_with_score)
        assert scoring_system.get_current_score(world_with_score) == 0

        # high score should remain
        assert scoring_system.get_high_score(world_with_score) == 100

    def test_high_score_updates_progressively(self, world_with_score, scoring_system):
        """Test high score updates as score increases."""
        scoring_system.on_apple_eaten(world_with_score, points=10)
        assert scoring_system.get_high_score(world_with_score) == 10

        scoring_system.on_apple_eaten(world_with_score, points=20)
        assert scoring_system.get_high_score(world_with_score) == 30

        scoring_system.on_apple_eaten(world_with_score, points=15)
        assert scoring_system.get_high_score(world_with_score) == 45

    def test_high_score_survives_multiple_resets(
        self, world_with_score, scoring_system
    ):
        """Test high score persists across multiple game resets."""
        # game 1
        scoring_system.on_apple_eaten(world_with_score, points=50)
        scoring_system.reset_current_score(world_with_score)

        # game 2
        scoring_system.on_apple_eaten(world_with_score, points=30)
        scoring_system.reset_current_score(world_with_score)

        # game 3
        scoring_system.on_apple_eaten(world_with_score, points=70)

        # high score should be 70 (highest across all games)
        assert scoring_system.get_high_score(world_with_score) == 70


class TestSnakeLengthScoring:
    """Test score updates based on snake length."""

    def test_update_score_from_snake_length(self, world_with_score, scoring_system):
        """Test updating score based on snake tail length."""
        scoring_system.update_score_from_snake_length(
            world_with_score, snake_tail_length=5
        )

        current_score = scoring_system.get_current_score(world_with_score)
        assert current_score == 5

    def test_score_updates_as_snake_grows(self, world_with_score, scoring_system):
        """Test score updates as snake grows."""
        scoring_system.update_score_from_snake_length(
            world_with_score, snake_tail_length=1
        )
        assert scoring_system.get_current_score(world_with_score) == 1

        scoring_system.update_score_from_snake_length(
            world_with_score, snake_tail_length=3
        )
        assert scoring_system.get_current_score(world_with_score) == 3

        scoring_system.update_score_from_snake_length(
            world_with_score, snake_tail_length=10
        )
        assert scoring_system.get_current_score(world_with_score) == 10

    def test_snake_length_updates_high_score(self, world_with_score, scoring_system):
        """Test that snake length can update high score."""
        scoring_system.update_score_from_snake_length(
            world_with_score, snake_tail_length=25
        )

        assert scoring_system.get_high_score(world_with_score) == 25


class TestScoreReset:
    """Test score reset functionality."""

    def test_reset_current_score_to_zero(self, world_with_score, scoring_system):
        """Test resetting current score to 0."""
        scoring_system.on_apple_eaten(world_with_score, points=50)
        assert scoring_system.get_current_score(world_with_score) == 50

        scoring_system.reset_current_score(world_with_score)
        assert scoring_system.get_current_score(world_with_score) == 0

    def test_reset_preserves_high_score(self, world_with_score, scoring_system):
        """Test that reset preserves high score."""
        scoring_system.on_apple_eaten(world_with_score, points=100)
        high_score_before = scoring_system.get_high_score(world_with_score)

        scoring_system.reset_current_score(world_with_score)

        high_score_after = scoring_system.get_high_score(world_with_score)
        assert high_score_before == high_score_after == 100

    def test_reset_on_empty_world(self, world, scoring_system):
        """Test reset when no score entity exists."""
        # should not crash
        scoring_system.reset_current_score(world)


class TestScoreGetters:
    """Test score getter methods."""

    def test_get_current_score_returns_zero_by_default(
        self, world_with_score, scoring_system
    ):
        """Test getting current score when it's 0."""
        current_score = scoring_system.get_current_score(world_with_score)
        assert current_score == 0

    def test_get_high_score_returns_zero_by_default(
        self, world_with_score, scoring_system
    ):
        """Test getting high score when it's 0."""
        high_score = scoring_system.get_high_score(world_with_score)
        assert high_score == 0

    def test_get_scores_returns_both(self, world_with_score, scoring_system):
        """Test getting both scores at once."""
        scoring_system.on_apple_eaten(world_with_score, points=30)

        current, high = scoring_system.get_scores(world_with_score)
        assert current == 30
        assert high == 30

    def test_get_scores_after_reset(self, world_with_score, scoring_system):
        """Test getting scores after reset."""
        scoring_system.on_apple_eaten(world_with_score, points=50)
        scoring_system.reset_current_score(world_with_score)

        current, high = scoring_system.get_scores(world_with_score)
        assert current == 0
        assert high == 50

    def test_get_scores_on_empty_world(self, world, scoring_system):
        """Test getting scores when no score entity exists."""
        current, high = scoring_system.get_scores(world)
        assert current == 0
        assert high == 0


class TestHighScoreSetter:
    """Test setting high score explicitly."""

    def test_set_high_score_directly(self, world_with_score, scoring_system):
        """Test setting high score to specific value."""
        scoring_system.set_high_score(world_with_score, 1000)

        high_score = scoring_system.get_high_score(world_with_score)
        assert high_score == 1000

    def test_set_high_score_for_loaded_saves(self, world_with_score, scoring_system):
        """Test setting high score when loading saved game."""
        # simulate loading high score from save file
        scoring_system.set_high_score(world_with_score, 500)

        # player plays and gets lower score
        scoring_system.on_apple_eaten(world_with_score, points=100)

        # high score should remain 500
        assert scoring_system.get_high_score(world_with_score) == 500

    def test_set_high_score_can_be_exceeded(self, world_with_score, scoring_system):
        """Test that set high score can still be exceeded."""
        scoring_system.set_high_score(world_with_score, 200)

        # player beats the high score
        scoring_system.on_apple_eaten(world_with_score, points=250)

        # high score should update
        assert scoring_system.get_high_score(world_with_score) == 250


class TestScoreCallback:
    """Test score callback functionality."""

    def test_callback_called_on_score_update(self, world_with_score):
        """Test that callback is called when score updates."""
        callback_calls = []

        def score_callback(current, high):
            callback_calls.append((current, high))

        system = ScoringSystem(score_callback=score_callback)

        system.on_apple_eaten(world_with_score, points=10)

        assert len(callback_calls) == 1
        assert callback_calls[0] == (10, 10)

    def test_callback_called_multiple_times(self, world_with_score):
        """Test callback called for each update."""
        callback_calls = []

        def score_callback(current, high):
            callback_calls.append((current, high))

        system = ScoringSystem(score_callback=score_callback)

        system.on_apple_eaten(world_with_score, points=10)
        system.on_apple_eaten(world_with_score, points=20)

        assert len(callback_calls) == 2
        assert callback_calls[0] == (10, 10)
        assert callback_calls[1] == (30, 30)

    def test_callback_called_on_reset(self, world_with_score):
        """Test callback called on score reset."""
        callback_calls = []

        def score_callback(current, high):
            callback_calls.append((current, high))

        system = ScoringSystem(score_callback=score_callback)

        system.on_apple_eaten(world_with_score, points=50)
        system.reset_current_score(world_with_score)

        assert len(callback_calls) == 2
        assert callback_calls[1] == (0, 50)  # reset but high score preserved


class TestScorePreservation:
    """Test score preservation across settings changes."""

    def test_high_score_preserved_across_world_changes(self, board):
        """Test that high score can be transferred between worlds."""
        # world 1 (before settings change)
        world1 = World(board)
        score_entity1 = ScoreEntity(current=0, high_score=0)
        world1.registry.add(score_entity1)

        system = ScoringSystem()
        system.on_apple_eaten(world1, points=100)

        # get high score before change
        high_score_before = system.get_high_score(world1)

        # world 2 (after settings change)
        world2 = World(board)
        score_entity2 = ScoreEntity(current=0, high_score=high_score_before)
        world2.registry.add(score_entity2)

        # high score should be preserved
        high_score_after = system.get_high_score(world2)
        assert high_score_after == high_score_before == 100


class TestIntegration:
    """Integration tests for ScoringSystem."""

    def test_full_game_workflow(self, world_with_score, scoring_system):
        """Test complete game workflow with scoring."""
        # start game
        assert scoring_system.get_current_score(world_with_score) == 0

        # eat some apples
        for _ in range(5):
            scoring_system.on_apple_eaten(world_with_score, points=10)

        assert scoring_system.get_current_score(world_with_score) == 50
        assert scoring_system.get_high_score(world_with_score) == 50

        # game over, reset
        scoring_system.reset_current_score(world_with_score)

        # new game, worse performance
        for _ in range(3):
            scoring_system.on_apple_eaten(world_with_score, points=10)

        assert scoring_system.get_current_score(world_with_score) == 30
        assert scoring_system.get_high_score(world_with_score) == 50  # preserved

        # game over, reset
        scoring_system.reset_current_score(world_with_score)

        # new game, beat high score
        for _ in range(7):
            scoring_system.on_apple_eaten(world_with_score, points=10)

        assert scoring_system.get_current_score(world_with_score) == 70
        assert scoring_system.get_high_score(world_with_score) == 70  # updated

    def test_mixed_scoring_methods(self, world_with_score, scoring_system):
        """Test using both apple eaten and snake length scoring."""
        # score from snake length
        scoring_system.update_score_from_snake_length(
            world_with_score, snake_tail_length=10
        )
        assert scoring_system.get_current_score(world_with_score) == 10

        # can still use apple eaten (though in real game, only one method is used)
        scoring_system.on_apple_eaten(world_with_score, points=5)
        assert scoring_system.get_current_score(world_with_score) == 15
