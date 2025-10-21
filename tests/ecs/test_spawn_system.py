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

"""Spawn system tests."""

import pytest

from src.ecs.world import World
from src.ecs.board import Board
from src.ecs.systems.spawn import SpawnSystem
from src.ecs.entities.snake import Snake
from src.ecs.entities.entity import EntityType
from src.ecs.components.position import Position
from src.ecs.components.velocity import Velocity
from src.ecs.components.snake_body import SnakeBody
from src.ecs.components.interpolation import Interpolation
from src.ecs.components.renderable import Renderable
from src.ecs.components.palette import Palette
from src.core.types.color import Color


@pytest.fixture
def small_board():
    """Create a small 3x3 board for testing (90x90 pixels with 30px cells)."""
    return Board(width=3, height=3, cell_size=30)


@pytest.fixture
def world_small(small_board):
    """Create a world with small board."""
    return World(small_board)


@pytest.fixture
def spawn_system():
    """Create a SpawnSystem with deterministic random seed."""
    return SpawnSystem(max_spawn_attempts=100, random_seed=42)


class TestSpawnSystemInitialization:
    """Test SpawnSystem initialization."""

    def test_spawn_system_created_successfully(self):
        """Test that SpawnSystem can be initialized."""
        system = SpawnSystem()
        assert system is not None

    def test_spawn_system_with_custom_params(self):
        """Test SpawnSystem with custom parameters."""
        system = SpawnSystem(
            max_spawn_attempts=500,
            apple_color=(200, 0, 0),
            random_seed=123,
        )
        assert system._max_spawn_attempts == 500
        assert system._apple_color == (200, 0, 0)


class TestSpawnApple:
    """Test spawning individual apples."""

    def test_spawn_apple_on_empty_board(self, world_small, spawn_system):
        """Test spawning apple on completely empty board."""
        apple_id = spawn_system.spawn_apple(world_small)

        assert apple_id is not None
        assert world_small.registry.has(apple_id)

        # verify entity is an apple
        apple = world_small.registry.get(apple_id)
        assert apple.get_type() == EntityType.APPLE
        assert hasattr(apple, "position")
        assert hasattr(apple, "edible")
        assert hasattr(apple, "renderable")

    def test_spawn_apple_has_valid_position(self, world_small, spawn_system):
        """Test that spawned apple has position within grid."""
        apple_id = spawn_system.spawn_apple(world_small)
        apple = world_small.registry.get(apple_id)

        board = world_small.board
        grid_size = board.cell_size

        # position should be grid-aligned
        assert apple.position.x % grid_size == 0
        assert apple.position.y % grid_size == 0

        # position should be within board bounds (in pixels)
        assert 0 <= apple.position.x < board.width * grid_size
        assert 0 <= apple.position.y < board.height * grid_size

    def test_spawn_apple_has_edible_component(self, world_small, spawn_system):
        """Test that spawned apple has edible component with points."""
        apple_id = spawn_system.spawn_apple(world_small)
        apple = world_small.registry.get(apple_id)

        assert apple.edible.points == 10
        assert apple.edible.growth == 1

    def test_spawn_apple_avoids_occupied_cells(self, world_small, spawn_system):
        """Test that apple spawns in unoccupied cell."""
        # create snake at position (0, 0)
        snake = Snake(
            position=Position(x=0, y=0),
            velocity=Velocity(dx=1, dy=0),
            body=SnakeBody(),
            interpolation=Interpolation(),
            renderable=Renderable(shape="square", color=Color(0, 255, 0), size=30),
            palette=Palette(),
        )
        world_small.registry.add(snake)

        # spawn apple - should avoid (0, 0)
        apple_id = spawn_system.spawn_apple(world_small)
        apple = world_small.registry.get(apple_id)

        # apple should not be at snake position
        assert not (apple.position.x == 0 and apple.position.y == 0)

    def test_spawn_apple_returns_none_when_board_full(self, world_small, spawn_system):
        """Test that spawn_apple returns None when no free cells."""
        # fill all 9 cells with entities
        for y in range(3):
            for x in range(3):
                snake = Snake(
                    position=Position(x=x * 30, y=y * 30),
                    velocity=Velocity(),
                    body=SnakeBody(),
                    interpolation=Interpolation(),
                    renderable=Renderable(
                        shape="square", color=Color(0, 255, 0), size=30
                    ),
                    palette=Palette(),
                )
                world_small.registry.add(snake)

        # try to spawn apple - should return None
        apple_id = spawn_system.spawn_apple(world_small)
        assert apple_id is None


class TestSpawnMultipleApples:
    """Test spawning multiple apples."""

    def test_spawn_multiple_apples_on_empty_board(self, world_small, spawn_system):
        """Test spawning multiple apples on empty board."""
        apple_ids = spawn_system.spawn_multiple_apples(world_small, count=3)

        assert len(apple_ids) == 3
        assert all(world_small.registry.has(aid) for aid in apple_ids)

    def test_spawn_multiple_apples_at_different_positions(
        self, world_small, spawn_system
    ):
        """Test that multiple apples spawn at different positions."""
        apple_ids = spawn_system.spawn_multiple_apples(world_small, count=3)

        positions = set()
        for apple_id in apple_ids:
            apple = world_small.registry.get(apple_id)
            positions.add((apple.position.x, apple.position.y))

        # all apples should have unique positions
        assert len(positions) == 3

    def test_spawn_multiple_apples_stops_when_board_full(
        self, world_small, spawn_system
    ):
        """Test that spawning stops when board is full."""
        # try to spawn 20 apples on 3x3 board (only 9 cells)
        apple_ids = spawn_system.spawn_multiple_apples(world_small, count=20)

        # should only spawn up to 9 apples (board capacity)
        assert len(apple_ids) <= 9


class TestFreeCellsCount:
    """Test free cells counting."""

    def test_free_cells_count_on_empty_board(self, world_small, spawn_system):
        """Test counting free cells on empty board."""
        free_cells = spawn_system.get_free_cells_count(world_small)

        # 3x3 board = 9 cells, all free
        assert free_cells == 9

    def test_free_cells_count_with_one_entity(self, world_small, spawn_system):
        """Test free cells count with one entity."""
        # add snake at one position
        snake = Snake(
            position=Position(x=0, y=0),
            velocity=Velocity(),
            body=SnakeBody(),
            interpolation=Interpolation(),
            renderable=Renderable(shape="square", color=Color(0, 255, 0), size=30),
            palette=Palette(),
        )
        world_small.registry.add(snake)

        free_cells = spawn_system.get_free_cells_count(world_small)

        # 9 total - 1 occupied = 8 free
        assert free_cells == 8

    def test_free_cells_count_with_snake_body(self, world_small, spawn_system):
        """Test that snake body segments are counted as occupied."""
        # create snake with body segments
        snake = Snake(
            position=Position(x=0, y=0),
            velocity=Velocity(),
            body=SnakeBody(
                segments=[
                    Position(x=30, y=0),
                    Position(x=60, y=0),
                ],
                size=3,
            ),
            interpolation=Interpolation(),
            renderable=Renderable(shape="square", color=Color(0, 255, 0), size=30),
            palette=Palette(),
        )
        world_small.registry.add(snake)

        free_cells = spawn_system.get_free_cells_count(world_small)

        # 9 total - 1 head - 2 body segments = 6 free
        assert free_cells == 6

    def test_free_cells_count_with_full_board(self, world_small, spawn_system):
        """Test free cells count when board is completely full."""
        # fill all 9 cells
        for y in range(3):
            for x in range(3):
                snake = Snake(
                    position=Position(x=x * 30, y=y * 30),
                    velocity=Velocity(),
                    body=SnakeBody(),
                    interpolation=Interpolation(),
                    renderable=Renderable(
                        shape="square", color=Color(0, 255, 0), size=30
                    ),
                    palette=Palette(),
                )
                world_small.registry.add(snake)

        free_cells = spawn_system.get_free_cells_count(world_small)

        assert free_cells == 0


class TestOccupiedCells:
    """Test occupied cells detection."""

    def test_occupied_cells_empty_board(self, world_small, spawn_system):
        """Test that empty board has no occupied cells."""
        occupied = spawn_system._get_occupied_cells(world_small)

        assert len(occupied) == 0

    def test_occupied_cells_with_entities(self, world_small, spawn_system):
        """Test occupied cells detection with multiple entities."""
        # add entities at specific positions
        positions = [(0, 0), (30, 30), (60, 60)]
        for x, y in positions:
            snake = Snake(
                position=Position(x=x, y=y),
                velocity=Velocity(),
                body=SnakeBody(),
                interpolation=Interpolation(),
                renderable=Renderable(shape="square", color=Color(0, 255, 0), size=30),
                palette=Palette(),
            )
            world_small.registry.add(snake)

        occupied = spawn_system._get_occupied_cells(world_small)

        assert len(occupied) == 3
        assert (0, 0) in occupied
        assert (30, 30) in occupied
        assert (60, 60) in occupied


class TestSpawnSystemIntegration:
    """Integration tests for SpawnSystem."""

    def test_spawn_apple_after_eating(self, world_small, spawn_system):
        """Test typical gameplay scenario: spawn apple after one is eaten."""
        # spawn initial apple
        apple1_id = spawn_system.spawn_apple(world_small)
        assert apple1_id is not None

        # simulate eating by removing apple
        world_small.registry.remove(apple1_id)

        # spawn new apple
        apple2_id = spawn_system.spawn_apple(world_small)
        assert apple2_id is not None
        assert apple2_id != apple1_id

    def test_spawn_maintains_apple_count(self, world_small, spawn_system):
        """Test that spawning maintains desired apple count."""
        target_count = 3

        # spawn initial apples
        apple_ids = spawn_system.spawn_multiple_apples(world_small, target_count)
        assert len(apple_ids) == target_count

        # verify correct number of apples exist
        apples = world_small.registry.query_by_type(EntityType.APPLE)
        assert len(apples) == target_count


class TestDeterministicSpawning:
    """Test deterministic spawning behavior."""

    def test_deterministic_spawn_with_seed(self):
        """Test that same seed produces same spawn positions."""
        # create two systems with same seed
        system1 = SpawnSystem(random_seed=42)
        system2 = SpawnSystem(random_seed=42)

        # create two identical worlds
        board1 = Board(width=10, height=10, cell_size=30)
        world1 = World(board1)

        board2 = Board(width=10, height=10, cell_size=30)
        world2 = World(board2)

        # spawn apples with both systems
        apple1_id = system1.spawn_apple(world1)
        apple2_id = system2.spawn_apple(world2)

        apple1 = world1.registry.get(apple1_id)
        apple2 = world2.registry.get(apple2_id)

        # should spawn at same position
        assert apple1.position.x == apple2.position.x
        assert apple1.position.y == apple2.position.y
