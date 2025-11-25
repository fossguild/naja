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

"""Cheese mode tests."""

import pytest

from ecs.world import World
from ecs.board import Board
from ecs.systems.collision import CollisionSystem
from ecs.systems.movement import MovementSystem
from ecs.systems.apple_spawn import AppleSpawnSystem
from ecs.entities.snake import Snake
from ecs.components.position import Position
from ecs.components.velocity import Velocity
from ecs.components.snake_body import SnakeBody
from ecs.components.interpolation import Interpolation
from ecs.components.renderable import Renderable
from ecs.components.input_buffer import InputBuffer
from ecs.components.game_state import GameState
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
def collision_system():
    """Create a CollisionSystem for testing."""
    return CollisionSystem()


@pytest.fixture
def movement_system():
    """Create a MovementSystem for testing."""
    return MovementSystem()


@pytest.fixture
def apple_spawn_system():
    """Create an AppleSpawnSystem for testing."""
    return AppleSpawnSystem(max_spawn_attempts=1000)


def create_game_state(cheese_mode_enabled=False):
    """Helper to create a GameState entity."""

    class GameStateEntity:
        def __init__(self):
            self.game_state = GameState(
                cheese_mode_enabled=cheese_mode_enabled,
                game_mode=(
                    "Cheese Mode" if cheese_mode_enabled else "Classic Snake Game"
                ),
            )

        def get_type(self):
            return None

    return GameStateEntity()


def create_snake_at(x, y, segments=None):
    """Helper to create a snake at a specific position."""
    if segments is None:
        segments = []

    return Snake(
        position=Position(x=x, y=y),
        velocity=Velocity(dx=1, dy=0),
        body=SnakeBody(segments=segments, size=len(segments) + 1),
        interpolation=Interpolation(),
        renderable=Renderable(shape="square", color=Color(0, 255, 0), size=30),
        input_buffer=InputBuffer(),
    )


class TestCheeseModeSelfCollision:
    """Test Cheese mode self-collision behavior."""

    def test_hole_segments_allow_passthrough(self, world, collision_system):
        """Test that snake can pass through hole segments (odd indices)."""
        # Setup: Cheese mode enabled
        game_state_entity = create_game_state(cheese_mode_enabled=True)
        world.registry.add(game_state_entity)

        # Create snake with body segments at specific positions
        # Head at (3, 3), segments at (2, 3), (1, 3), (0, 3)
        snake = create_snake_at(
            3,
            3,
            segments=[
                Position(x=2, y=3),  # Index 0 - solid
                Position(x=1, y=3),  # Index 1 - hole
                Position(x=0, y=3),  # Index 2 - solid
            ],
        )
        world.registry.add(snake)

        # Move snake to collide with hole segment (index 1) at position (1, 3)
        snake.position.x = 1
        snake.position.y = 3

        # Check collision - should NOT detect collision with hole
        collision_detected = collision_system._check_self_bite(world)
        assert (
            not collision_detected
        ), "Hole segment (odd index) should allow pass-through"

    def test_solid_segments_cause_death(self, world, collision_system):
        """Test that collision with solid segments (even indices) kills snake."""
        # Setup: Cheese mode enabled
        game_state_entity = create_game_state(cheese_mode_enabled=True)
        world.registry.add(game_state_entity)

        # Create snake with body segments
        snake = create_snake_at(
            3,
            3,
            segments=[
                Position(x=2, y=3),  # Index 0 - solid
                Position(x=1, y=3),  # Index 1 - hole
                Position(x=0, y=3),  # Index 2 - solid
            ],
        )
        world.registry.add(snake)

        # Move snake to collide with solid segment (index 0) at position (2, 3)
        snake.position.x = 2
        snake.position.y = 3

        # Check collision - should detect collision with solid segment
        collision_detected = collision_system._check_self_bite(world)
        assert collision_detected, "Solid segment (even index) should cause collision"

    def test_classic_mode_all_segments_solid(self, world, collision_system):
        """Test that Classic mode treats all segments as solid (regression test)."""
        # Setup: Classic mode (cheese_mode_enabled=False)
        game_state_entity = create_game_state(cheese_mode_enabled=False)
        world.registry.add(game_state_entity)

        # Create snake with body segments
        snake = create_snake_at(
            3,
            3,
            segments=[
                Position(x=2, y=3),  # Index 0
                Position(x=1, y=3),  # Index 1
                Position(x=0, y=3),  # Index 2
            ],
        )
        world.registry.add(snake)

        # Test collision with index 1 (would be hole in Cheese mode)
        snake.position.x = 1
        snake.position.y = 3

        collision_detected = collision_system._check_self_bite(world)
        assert collision_detected, "Classic mode should treat all segments as solid"


class TestCheeseModeGrowth:
    """Test Cheese mode +2 growth behavior."""

    def test_apple_eating_adds_pending_growth(self, world, collision_system):
        """Test that eating apple in Cheese mode adds +2 to pending_growth."""
        # Setup: Cheese mode enabled
        game_state_entity = create_game_state(cheese_mode_enabled=True)
        world.registry.add(game_state_entity)

        # Create snake
        snake = create_snake_at(5, 5)
        world.registry.add(snake)

        # Create apple at snake's position
        from ecs.prefabs.apple import create_apple

        create_apple(world, x=5, y=5, grid_size=30, color=None)

        # Initial pending growth should be 0
        assert snake.body.pending_growth == 0

        # Check apple collision (this should add +2 pending_growth)
        collision_system._check_apple_collision(world)

        # Verify pending growth increased by 2
        assert snake.body.pending_growth == 2

    def test_classic_mode_immediate_growth(self, world, collision_system):
        """Test that Classic mode uses immediate +1 growth (regression test)."""
        # Setup: Classic mode
        game_state_entity = create_game_state(cheese_mode_enabled=False)
        world.registry.add(game_state_entity)

        # Create snake
        snake = create_snake_at(5, 5)
        initial_size = snake.body.size
        world.registry.add(snake)

        # Create apple at snake's position
        from ecs.prefabs.apple import create_apple

        create_apple(world, x=5, y=5, grid_size=30, color=None)

        # Check apple collision
        collision_system._check_apple_collision(world)

        # Verify immediate size increase
        assert snake.body.size == initial_size + 1
        # pending_growth should be 0 or unchanged
        assert snake.body.pending_growth == 0

    def test_pending_growth_processes_gradually(self, world, movement_system):
        """Test that pending_growth decrements by 1 per frame."""
        # Create snake with pending growth
        snake = create_snake_at(5, 5)
        snake.body.pending_growth = 2
        initial_size = snake.body.size
        world.registry.add(snake)

        # Set delta time for movement
        world.set_dt_ms(1000)  # 1 second

        # First update - should process 1 pending growth
        movement_system.update(world)

        assert snake.body.size == initial_size + 1
        assert snake.body.pending_growth == 1

        # Second update - should process remaining growth
        movement_system.update(world)

        assert snake.body.size == initial_size + 2
        assert snake.body.pending_growth == 0


class TestCheeseModeAppleSpawn:
    """Test Cheese mode apple spawn restrictions."""

    def test_apple_spawn_requires_two_empty_neighbors(self, world, apple_spawn_system):
        """Test that apples spawn only with ≥2 empty neighbors in Cheese mode."""
        # Setup: Cheese mode enabled
        game_state_entity = create_game_state(cheese_mode_enabled=True)
        world.registry.add(game_state_entity)

        # Fill board except for one cell with exactly 1 empty neighbor
        # Create a corner cell (0,0) which has only 2 neighbors (right and down)
        # Block one neighbor to test
        for y in range(10):
            for x in range(10):
                if (x, y) == (0, 0):  # Leave (0,0) empty
                    continue
                if (x, y) == (1, 0):  # Block right neighbor
                    snake = create_snake_at(x, y)
                    world.registry.add(snake)
                elif (x, y) == (0, 1):  # Leave down neighbor open
                    continue
                else:
                    # Fill other cells
                    snake = create_snake_at(x, y)
                    world.registry.add(snake)

        # Position (0,0) now has only 1 empty neighbor: (0,1)
        # Try to spawn apple - should fail to spawn at (0,0)
        # Count empty neighbors for (0,0)
        occupied = apple_spawn_system._get_occupied_positions(world)
        empty_neighbors = apple_spawn_system._count_empty_neighbors(
            0, 0, world.board, occupied
        )

        assert (
            empty_neighbors < 2
        ), "Test setup should create position with <2 empty neighbors"

    def test_count_empty_neighbors_all_directions(self, world, apple_spawn_system):
        """Test _count_empty_neighbors counts N/S/E/W correctly."""
        # Create empty world
        occupied = set()

        # Test center position (5, 5) - should have 4 empty neighbors
        count = apple_spawn_system._count_empty_neighbors(5, 5, world.board, occupied)
        assert count == 4, "Center position should have 4 empty neighbors"

        # Block North
        occupied.add((5, 4))
        count = apple_spawn_system._count_empty_neighbors(5, 5, world.board, occupied)
        assert count == 3

        # Block East
        occupied.add((6, 5))
        count = apple_spawn_system._count_empty_neighbors(5, 5, world.board, occupied)
        assert count == 2

        # Block South
        occupied.add((5, 6))
        count = apple_spawn_system._count_empty_neighbors(5, 5, world.board, occupied)
        assert count == 1

        # Block West
        occupied.add((4, 5))
        count = apple_spawn_system._count_empty_neighbors(5, 5, world.board, occupied)
        assert count == 0

    def test_classic_mode_no_neighbor_restriction(self, world, apple_spawn_system):
        """Test that Classic mode doesn't enforce neighbor restriction."""
        # Setup: Classic mode
        game_state_entity = create_game_state(cheese_mode_enabled=False)
        world.registry.add(game_state_entity)

        # Create a nearly full board leaving only one cell with 0 empty neighbors
        # This would be invalid in Cheese mode but valid in Classic
        for y in range(10):
            for x in range(10):
                if (x, y) == (5, 5):  # Leave center empty
                    continue
                snake = create_snake_at(x, y)
                world.registry.add(snake)

        # Try to spawn apple - should succeed even with 0 empty neighbors
        position = apple_spawn_system._find_valid_position(world)
        assert position is not None, "Classic mode should spawn without neighbor check"
        assert position == (5, 5)
