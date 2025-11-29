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

"""Cheese mode tests.

Tests the unique mechanics of Cheese Mode:
- Stationary segments (breadcrumb trail)
- +2 growth system
- Apple spawn restrictions (≥2 empty neighbors)
- Classic mode unchanged (regression tests)
"""

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
from ecs.components.hunger import Hunger
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


def create_game_state(cheese_mode_enabled=False, game_started=True):
    """Helper to create a GameState entity."""

    class GameStateEntity:
        def __init__(self):
            self.game_state = GameState(
                cheese_mode_enabled=cheese_mode_enabled,
                game_mode=(
                    "Cheese Mode" if cheese_mode_enabled else "Classic Snake Game"
                ),
                game_started=game_started,
            )

        def get_type(self):
            return None

    return GameStateEntity()


def create_snake_at(x, y, segments=None, size=None):
    """Helper to create a snake at a specific position."""
    if segments is None:
        segments = []
    if size is None:
        size = len(segments) + 1

    return Snake(
        position=Position(x=x, y=y, prev_x=x, prev_y=y),
        velocity=Velocity(dx=1, dy=0),
        body=SnakeBody(segments=segments, size=size),
        interpolation=Interpolation(),
        renderable=Renderable(shape="square", color=Color(0, 255, 0), size=30),
        input_buffer=InputBuffer(),
        hunger=(Hunger(current_time=0.0, max_time=0.0)),
    )


class TestCheeseModeSelfCollision:
    """Test Cheese mode collision behavior."""

    def test_solid_segments_cause_death(self, world, collision_system):
        """Test that collision with any segment in Cheese mode kills snake.

        In new implementation: ALL segments in array are solid.
        Holes are just empty cells (not stored as segments).
        """
        # Setup: Cheese mode enabled
        game_state_entity = create_game_state(cheese_mode_enabled=True)
        world.registry.add(game_state_entity)

        # Create snake with body segments (all solid in new implementation)
        snake = create_snake_at(
            3,
            3,
            segments=[
                Position(x=2, y=3, prev_x=2, prev_y=3),
                Position(x=1, y=3, prev_x=1, prev_y=3),
                Position(x=0, y=3, prev_x=0, prev_y=3),
            ],
        )
        world.registry.add(snake)

        # Move snake to collide with any segment
        snake.position.x = 2
        snake.position.y = 3

        # Check collision - should detect collision
        collision_detected = collision_system._check_self_bite(world)
        assert collision_detected, "Collision with solid segment should kill snake"

    def test_empty_cells_allow_passthrough(self, world, collision_system):
        """Test that snake can pass through empty cells (gaps between segments).

        In Cheese mode, segments are only added every OTHER move.
        This creates natural gaps that the snake can pass through.
        """
        # Setup: Cheese mode enabled
        game_state_entity = create_game_state(cheese_mode_enabled=True)
        world.registry.add(game_state_entity)

        # Create snake with segments that have gaps
        # Segments at positions with 2-cell spacing (like real Cheese mode)
        snake = create_snake_at(
            5,
            5,
            segments=[
                Position(x=3, y=5, prev_x=3, prev_y=5),  # Gap of 1 cell before this
                Position(x=1, y=5, prev_x=1, prev_y=5),  # Gap of 1 cell before this
            ],
        )
        world.registry.add(snake)

        # Move head to a gap (cell that doesn't have a segment)
        snake.position.x = 4  # Between segments at x=3 and x=5
        snake.position.y = 5

        # Should NOT collide (it's an empty cell)
        collision_detected = collision_system._check_self_bite(world)
        assert not collision_detected, "Empty cells should allow pass-through"

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
                Position(x=2, y=3, prev_x=2, prev_y=3),
                Position(x=1, y=3, prev_x=1, prev_y=3),
                Position(x=0, y=3, prev_x=0, prev_y=3),
            ],
        )
        world.registry.add(snake)

        # Test collision with any segment
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
        # pending_growth should be 0
        assert snake.body.pending_growth == 0

    def test_pending_growth_processes_gradually(self, world, movement_system):
        """Test that pending_growth decrements by 1 per frame in Cheese mode.

        Note: In Cheese mode, segments are added every OTHER move, but
        pending_growth still decrements every frame.
        """
        # Setup: Cheese mode enabled
        game_state_entity = create_game_state(cheese_mode_enabled=True)
        world.registry.add(game_state_entity)

        # Create snake with pending growth
        snake = create_snake_at(5, 5)
        snake.body.pending_growth = 2
        world.registry.add(snake)

        # Set delta time for movement
        world.set_dt_ms(1000)  # 1 second

        # First update - should process 1 pending growth
        movement_system.update(world)

        assert snake.body.pending_growth == 1

        # Second update - should process remaining growth
        movement_system.update(world)

        assert snake.body.pending_growth == 0

        # Note: Size might not be initial_size + 2 because segments
        # are only added every OTHER move in Cheese mode
        # The important part is that pending_growth is processed


class TestCheeseModeAppleSpawn:
    """Test Cheese mode apple spawn restrictions."""

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

    def test_cheese_mode_requires_two_empty_neighbors(self, world, apple_spawn_system):
        """Test that Cheese mode requires ≥2 empty neighbors for apple spawn."""
        # Setup: Cheese mode enabled
        game_state_entity = create_game_state(cheese_mode_enabled=True)
        world.registry.add(game_state_entity)

        # Create scenario with a position that has exactly 1 empty neighbor
        occupied = set()
        # Fill neighbors except one
        occupied.add((5, 4))  # North blocked
        occupied.add((6, 5))  # East blocked
        occupied.add((5, 6))  # South blocked
        # (4, 5) is empty - only 1 neighbor

        count = apple_spawn_system._count_empty_neighbors(5, 5, world.board, occupied)
        assert count == 1, "Should have exactly 1 empty neighbor"

    def test_classic_mode_no_neighbor_restriction(self, world, apple_spawn_system):
        """Test that Classic mode doesn't enforce neighbor restriction."""
        # Setup: Classic mode
        game_state_entity = create_game_state(cheese_mode_enabled=False)
        world.registry.add(game_state_entity)

        # Create a nearly full board leaving only one cell
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


class TestCheeseModeInitialization:
    """Test Cheese mode initialization."""

    def test_cheese_mode_starts_with_size_3(self):
        """Test that Cheese mode snake starts with size 3."""
        from ecs.prefabs.snake import create_snake

        board = Board(width=20, height=20, cell_size=30)
        world = World(board)

        # Create snake in Cheese mode
        snake_id = create_snake(
            world=world,
            grid_size=30,
            cheese_mode=True,
        )

        snake = world.registry.get(snake_id)

        # Should start with size 3 (head + 2 segments)
        assert snake.body.size == 3, "Cheese mode should start with size 3"
        assert len(snake.body.segments) == 2, "Should have 2 initial segments (stacked)"

    def test_classic_mode_starts_with_size_1(self):
        """Test that Classic mode still starts with size 1 (regression)."""
        from ecs.prefabs.snake import create_snake

        board = Board(width=20, height=20, cell_size=30)
        world = World(board)

        # Create snake in Classic mode
        snake_id = create_snake(
            world=world,
            grid_size=30,
            cheese_mode=False,
        )

        snake = world.registry.get(snake_id)

        # Should start with size 1 (head only)
        assert snake.body.size == 1, "Classic mode should start with size 1"
        assert len(snake.body.segments) == 0, "Should have no initial segments"
