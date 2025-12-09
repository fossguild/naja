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

"""Trail Mode tests.

Tests the unique mechanics of Trail Mode:
- Trail obstacles created at previous head positions
- Trail obstacles persist throughout the game
- Trail obstacles cause collision/death
- Classic mode unchanged (regression tests)
"""

import pytest

from ecs.world import World
from ecs.board import Board
from ecs.systems.trail_generation import TrailGenerationSystem
from ecs.systems.movement import MovementSystem
from ecs.systems.collision import CollisionSystem
from ecs.entities.snake import Snake
from ecs.components.position import Position
from ecs.components.velocity import Velocity
from ecs.components.snake_body import SnakeBody
from ecs.components.interpolation import Interpolation
from ecs.components.renderable import Renderable
from ecs.components.input_buffer import InputBuffer
from ecs.components.game_state import GameState
from ecs.components.hunger import Hunger
from ecs.entities.entity import EntityType
from core.types.color import Color


@pytest.fixture
def board():
    """Create a 10x10 board for testing."""
    return Board(width=10, height=10, cell_size=30)


@pytest.fixture
def world(board):
    """Create a world with board."""
    return World(board)


@pytest.fixture
def trail_system():
    """Create a TrailGenerationSystem for testing."""
    return TrailGenerationSystem()


@pytest.fixture
def movement_system():
    """Create a MovementSystem for testing."""
    return MovementSystem()


@pytest.fixture
def collision_system():
    """Create a CollisionSystem for testing."""
    return CollisionSystem()


def create_game_state(trail_mode_enabled=False, game_started=True):
    """Helper to create a GameState entity."""

    class GameStateEntity:
        def __init__(self):
            self.game_state = GameState(
                trail_mode_enabled=trail_mode_enabled,
                game_mode=(
                    "Trail Mode" if trail_mode_enabled else "Classic Snake Game"
                ),
                game_started=game_started,
            )

        def get_type(self):
            return None

    return GameStateEntity()


def create_snake_at(x, y, dx=1, dy=0):
    """Helper to create a snake at a specific position."""
    return Snake(
        position=Position(x=x, y=y, prev_x=x, prev_y=y),
        velocity=Velocity(dx=dx, dy=dy),
        body=SnakeBody(segments=[], size=1),
        interpolation=Interpolation(),
        renderable=Renderable(shape="square", color=Color(0, 255, 0), size=30),
        input_buffer=InputBuffer(),
        hunger=Hunger(current_time=0.0, max_time=0.0),
    )


class TestTrailModeBasics:
    """Test basic Trail Mode functionality."""

    def test_trail_system_creates_no_obstacles_when_disabled(self, world, trail_system):
        """Test that trail system does nothing when Trail Mode is disabled."""
        # Setup: Classic mode (trail_mode_enabled=False)
        game_state_entity = create_game_state(trail_mode_enabled=False)
        world.registry.add(game_state_entity)

        # Create snake
        snake = create_snake_at(5, 5)
        world.registry.add(snake)

        # Update trail system
        world.set_dt_ms(1000)
        trail_system.update(world)

        # Move snake
        snake.position.prev_x = snake.position.x
        snake.position.prev_y = snake.position.y
        snake.position.x = 6
        snake.position.y = 5

        # Update trail system again
        trail_system.update(world)

        # Verify no trail obstacles created
        obstacles = world.registry.query_by_type(EntityType.OBSTACLE)
        assert len(obstacles) == 0, "No obstacles should be created in Classic mode"

    def test_trail_system_creates_obstacle_at_previous_position(
        self, world, trail_system
    ):
        """Test that trail system creates obstacles where the snake was."""
        # Setup: Trail mode enabled
        game_state_entity = create_game_state(trail_mode_enabled=True)
        world.registry.add(game_state_entity)

        # Create snake at (5, 5)
        snake = create_snake_at(5, 5)
        world.registry.add(snake)

        # First update - establish initial position
        world.set_dt_ms(1000)
        trail_system.update(world)

        # No obstacles yet (snake hasn't moved)
        obstacles = world.registry.query_by_type(EntityType.OBSTACLE)
        assert len(obstacles) == 0

        # Move snake to (6, 5)
        snake.position.prev_x = snake.position.x
        snake.position.prev_y = snake.position.y
        snake.position.x = 6
        snake.position.y = 5

        # Update trail system - should create obstacle at (5, 5)
        trail_system.update(world)

        # Verify obstacle created at previous position
        obstacles = world.registry.query_by_type(EntityType.OBSTACLE)
        assert len(obstacles) == 1, "One obstacle should be created"

        obstacle = list(obstacles.values())[0]
        assert obstacle.position.x == 5
        assert obstacle.position.y == 5

    def test_trail_obstacles_persist(self, world, trail_system):
        """Test that trail obstacles remain after being created."""
        # Setup
        game_state_entity = create_game_state(trail_mode_enabled=True)
        world.registry.add(game_state_entity)

        snake = create_snake_at(5, 5)
        world.registry.add(snake)

        world.set_dt_ms(1000)
        trail_system.update(world)

        # Move snake multiple times
        positions = [(6, 5), (7, 5), (8, 5)]
        for new_x, new_y in positions:
            snake.position.prev_x = snake.position.x
            snake.position.prev_y = snake.position.y
            snake.position.x = new_x
            snake.position.y = new_y
            trail_system.update(world)

        # Verify all obstacles persist
        obstacles = world.registry.query_by_type(EntityType.OBSTACLE)
        assert len(obstacles) == 3, "All trail obstacles should persist"

    def test_no_duplicate_trail_obstacles(self, world, trail_system):
        """Test that trail system doesn't create duplicate obstacles at same position."""
        # Setup
        game_state_entity = create_game_state(trail_mode_enabled=True)
        world.registry.add(game_state_entity)

        snake = create_snake_at(5, 5, dx=1, dy=0)
        world.registry.add(snake)

        world.set_dt_ms(1000)
        trail_system.update(world)

        # Move snake forward then back to create potential duplicate
        snake.position.prev_x, snake.position.prev_y = 5, 5
        snake.position.x, snake.position.y = 6, 5
        trail_system.update(world)

        snake.position.prev_x, snake.position.prev_y = 6, 5
        snake.position.x, snake.position.y = 5, 5
        trail_system.update(world)

        # Count obstacles at (5, 5)
        obstacles = world.registry.query_by_type(EntityType.OBSTACLE)
        obstacles_at_5_5 = sum(
            1
            for obs in obstacles.values()
            if obs.position.x == 5 and obs.position.y == 5
        )
        assert obstacles_at_5_5 <= 1, "Should not create duplicate trail obstacles"


class TestTrailModeCollision:
    """Test Trail Mode collision behavior."""

    def test_collision_with_trail_obstacle_kills_snake(
        self, world, trail_system, collision_system
    ):
        """Test that colliding with trail obstacle causes death."""
        # Setup
        game_state_entity = create_game_state(trail_mode_enabled=True)
        world.registry.add(game_state_entity)

        snake = create_snake_at(5, 5)
        world.registry.add(snake)

        world.set_dt_ms(1000)
        trail_system.update(world)

        # Create trail at (6, 5)
        snake.position.prev_x, snake.position.prev_y = 5, 5
        snake.position.x, snake.position.y = 6, 5
        trail_system.update(world)

        # Move away
        snake.position.prev_x, snake.position.prev_y = 6, 5
        snake.position.x, snake.position.y = 7, 5
        trail_system.update(world)

        # Verify trail exists at (6, 5)
        obstacles = world.registry.query_by_type(EntityType.OBSTACLE)
        assert len(obstacles) >= 1

        # Move back into trail obstacle at (6, 5)
        snake.position.prev_x, snake.position.prev_y = 7, 5
        snake.position.x, snake.position.y = 6, 5

        # Check collision
        collision_detected = collision_system._check_obstacle_collision(world)
        assert collision_detected, "Collision with trail obstacle should be detected"


def test_trail_mode_integration(world, trail_system, movement_system):
    """Integration test: Trail Mode with MovementSystem."""
    # Setup
    game_state_entity = create_game_state(trail_mode_enabled=True)
    world.registry.add(game_state_entity)

    snake = create_snake_at(5, 5, dx=1, dy=0)
    world.registry.add(snake)

    world.set_dt_ms(1000)

    # Initial update
    trail_system.update(world)
    initial_obstacles = len(world.registry.query_by_type(EntityType.OBSTACLE))

    # Move and create trail
    movement_system.update(world)
    trail_system.update(world)

    # Verify trail obstacle created after movement
    obstacles_after_move = len(world.registry.query_by_type(EntityType.OBSTACLE))
    assert obstacles_after_move > initial_obstacles, (
        "Trail obstacle should be created after movement"
    )


class TestTrailDecaySystem:
    """Test Trail Decay functionality."""

    @pytest.fixture
    def decay_system(self):
        """Create a TrailDecaySystem for testing."""
        from ecs.systems.trail_decay import TrailDecaySystem

        return TrailDecaySystem()

    def test_decay_system_does_nothing_when_disabled(self, world, decay_system):
        """Test that decay system does nothing when Trail Mode is disabled."""
        from ecs.entities.trail_obstacle import TrailObstacle
        from ecs.components.trail_obstacle import TrailObstacleTag

        # Setup: Classic mode (trail_mode_enabled=False)
        game_state_entity = create_game_state(trail_mode_enabled=False)
        world.registry.add(game_state_entity)

        # Create a trail obstacle manually
        trail_obstacle = TrailObstacle(
            position=Position(x=5, y=5),
            tag=TrailObstacleTag(ttl=10, max_ttl=10),
            renderable=Renderable(shape="square", color=Color(74, 74, 74), size=30),
        )
        world.registry.add(trail_obstacle)

        # Create snake
        snake = create_snake_at(3, 3)
        world.registry.add(snake)

        # Update decay system
        world.set_dt_ms(1000)
        decay_system.update(world)

        # Verify TTL unchanged (obstacle should still exist with same TTL)
        obstacles = world.registry.query_by_type(EntityType.OBSTACLE)
        assert len(obstacles) == 1
        assert list(obstacles.values())[0].tag.ttl == 10

    def test_decay_system_decrements_ttl_on_snake_move(
        self, world, trail_system, decay_system
    ):
        """Test that trail obstacle TTL decrements when snake moves."""
        # Setup: Trail mode enabled
        game_state_entity = create_game_state(trail_mode_enabled=True)
        world.registry.add(game_state_entity)

        # Create snake at (5, 5)
        snake = create_snake_at(5, 5)
        world.registry.add(snake)

        # Initialize systems
        world.set_dt_ms(1000)
        trail_system.update(world)
        decay_system.update(world)

        # Move snake to (6, 5) - this creates a trail obstacle at (5, 5)
        snake.position.prev_x = snake.position.x
        snake.position.prev_y = snake.position.y
        snake.position.x = 6
        snake.position.y = 5

        trail_system.update(world)
        decay_system.update(world)

        # Get the trail obstacle
        obstacles = world.registry.query_by_type(EntityType.OBSTACLE)
        assert len(obstacles) == 1

        initial_ttl = list(obstacles.values())[0].tag.ttl

        # Move snake again to (7, 5)
        snake.position.prev_x = snake.position.x
        snake.position.prev_y = snake.position.y
        snake.position.x = 7
        snake.position.y = 5

        trail_system.update(world)
        decay_system.update(world)

        # Get obstacles again and check TTL decremented
        obstacles = world.registry.query_by_type(EntityType.OBSTACLE)
        # Find the first trail obstacle (created at position 5,5)
        first_obstacle = None
        for obs in obstacles.values():
            if obs.position.x == 5 and obs.position.y == 5:
                first_obstacle = obs
                break

        assert first_obstacle is not None
        assert first_obstacle.tag.ttl == initial_ttl - 1, "TTL should decrement on move"

    def test_decay_system_removes_expired_obstacles(
        self, world, trail_system, decay_system
    ):
        """Test that trail obstacles are removed when TTL reaches zero."""
        from ecs.entities.trail_obstacle import TrailObstacle
        from ecs.components.trail_obstacle import TrailObstacleTag

        # Setup: Trail mode enabled
        game_state_entity = create_game_state(trail_mode_enabled=True)
        world.registry.add(game_state_entity)

        # Create snake
        snake = create_snake_at(5, 5)
        world.registry.add(snake)

        # Create a trail obstacle with TTL of 1 (about to expire)
        trail_obstacle = TrailObstacle(
            position=Position(x=3, y=3),
            tag=TrailObstacleTag(ttl=1, max_ttl=10),
            renderable=Renderable(shape="square", color=Color(74, 74, 74), size=30),
        )
        world.registry.add(trail_obstacle)

        # Add position to game state trail_obstacles list
        game_state_entity.game_state.trail_obstacles.append((3, 3))

        # Initialize systems
        world.set_dt_ms(1000)
        trail_system.update(world)
        decay_system.update(world)

        # Verify obstacle exists
        obstacles = world.registry.query_by_type(EntityType.OBSTACLE)
        assert len(obstacles) == 1

        # Move snake to trigger decay
        snake.position.prev_x = snake.position.x
        snake.position.prev_y = snake.position.y
        snake.position.x = 6
        snake.position.y = 5

        trail_system.update(world)
        decay_system.update(world)

        # Check that position at (3, 3) was removed (TTL went from 1 to 0)
        obstacles = world.registry.query_by_type(EntityType.OBSTACLE)
        obstacle_at_3_3 = [
            obs
            for obs in obstacles.values()
            if obs.position.x == 3 and obs.position.y == 3
        ]
        assert len(obstacle_at_3_3) == 0, "Expired obstacle should be removed"

        # Verify it was also removed from game state
        assert (3, 3) not in game_state_entity.game_state.trail_obstacles

    def test_decay_system_fades_obstacle_color(self, world, decay_system):
        """Test that obstacle color fades as TTL decreases."""
        from ecs.entities.trail_obstacle import TrailObstacle
        from ecs.components.trail_obstacle import TrailObstacleTag

        # Setup: Trail mode enabled
        game_state_entity = create_game_state(trail_mode_enabled=True)
        world.registry.add(game_state_entity)

        # Create snake
        snake = create_snake_at(5, 5)
        world.registry.add(snake)

        # Create a trail obstacle with low TTL
        initial_color = Color(74, 74, 74)
        trail_obstacle = TrailObstacle(
            position=Position(x=3, y=3),
            tag=TrailObstacleTag(ttl=5, max_ttl=10),  # 50% life remaining
            renderable=Renderable(shape="square", color=initial_color, size=30),
        )
        world.registry.add(trail_obstacle)
        game_state_entity.game_state.trail_obstacles.append((3, 3))

        # Initialize systems
        world.set_dt_ms(1000)
        decay_system.update(world)

        # Move snake to trigger decay
        snake.position.prev_x = snake.position.x
        snake.position.prev_y = snake.position.y
        snake.position.x = 6
        snake.position.y = 5

        decay_system.update(world)

        # Get obstacle and check color changed
        obstacles = world.registry.query_by_type(EntityType.OBSTACLE)
        obstacle = [
            obs
            for obs in obstacles.values()
            if obs.position.x == 3 and obs.position.y == 3
        ][0]

        # Color should be different (faded) from initial
        current_color = obstacle.renderable.color
        # The color should have changed due to fade effect
        assert (
            current_color.r != initial_color.r
            or current_color.g != initial_color.g
            or current_color.b != initial_color.b
        ), "Color should fade as TTL decreases"

    def test_trail_opens_path_after_decay(
        self, world, trail_system, decay_system, collision_system
    ):
        """Test that snake can pass through position after trail decays."""
        from ecs.entities.trail_obstacle import TrailObstacle
        from ecs.components.trail_obstacle import TrailObstacleTag

        # Setup: Trail mode enabled
        game_state_entity = create_game_state(trail_mode_enabled=True)
        world.registry.add(game_state_entity)

        # Create snake
        snake = create_snake_at(5, 5)
        world.registry.add(snake)

        # Create a trail obstacle with TTL of 1 at position (6, 5)
        trail_obstacle = TrailObstacle(
            position=Position(x=6, y=5),
            tag=TrailObstacleTag(ttl=1, max_ttl=10),
            renderable=Renderable(shape="square", color=Color(74, 74, 74), size=30),
        )
        world.registry.add(trail_obstacle)
        game_state_entity.game_state.trail_obstacles.append((6, 5))

        world.set_dt_ms(1000)
        trail_system.update(world)
        decay_system.update(world)

        # Moving snake triggers decay (obstacle at 6,5 expires)
        snake.position.prev_x = snake.position.x
        snake.position.prev_y = snake.position.y
        snake.position.x = 4  # Move away first
        snake.position.y = 5

        trail_system.update(world)
        decay_system.update(world)

        # Now obstacle at (6, 5) should be gone
        obstacles = world.registry.query_by_type(EntityType.OBSTACLE)
        obstacle_at_6_5 = [
            obs
            for obs in obstacles.values()
            if obs.position.x == 6 and obs.position.y == 5
        ]
        assert len(obstacle_at_6_5) == 0, "Trail should have decayed"

        # Now snake can safely move to (6, 5)
        snake.position.prev_x = snake.position.x
        snake.position.prev_y = snake.position.y
        snake.position.x = 6
        snake.position.y = 5

        # Check no collision at the now-empty position
        collision_detected = collision_system._check_obstacle_collision(world)
        assert not collision_detected, "No collision after trail decays"
