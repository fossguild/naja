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

"""Tests for entity prefab factories."""

from src.ecs.world import World
from src.ecs.board import Board
from src.ecs.entities.entity import EntityType
from src.ecs.prefabs.snake import create_snake
from src.ecs.prefabs.apple import create_apple
from src.ecs.prefabs.obstacle_field import create_obstacles


class TestSnakePrefab:
    """Test suite for create_snake prefab factory."""

    def test_create_snake_basic(self):
        """Test basic snake creation."""
        # arrange
        board = Board(width=400, height=400, cell_size=20)
        world = World(board)

        # act
        snake_id = create_snake(world, grid_size=20)

        # assert
        assert world.registry.has(snake_id)
        snake = world.registry.get(snake_id)
        assert snake is not None
        assert snake.get_type() == EntityType.SNAKE

    def test_create_snake_position(self):
        """Test snake starts at correct position."""
        # arrange
        board = Board(width=400, height=400, cell_size=20)
        world = World(board)
        grid_size = 20

        # act
        snake_id = create_snake(world, grid_size=grid_size)
        snake = world.registry.get(snake_id)

        # assert - should start one cell from origin
        assert snake.position.x == grid_size
        assert snake.position.y == grid_size
        assert snake.position.prev_x == grid_size
        assert snake.position.prev_y == grid_size

    def test_create_snake_velocity(self):
        """Test snake has correct initial velocity."""
        # arrange
        board = Board(width=400, height=400, cell_size=20)
        world = World(board)

        # act
        snake_id = create_snake(world, grid_size=20, initial_speed=5.0)
        snake = world.registry.get(snake_id)

        # assert - should start moving right
        assert snake.velocity.dx == 1
        assert snake.velocity.dy == 0
        assert snake.velocity.speed == 5.0

    def test_create_snake_body(self):
        """Test snake has correct initial body state."""
        # arrange
        board = Board(width=400, height=400, cell_size=20)
        world = World(board)

        # act
        snake_id = create_snake(world, grid_size=20)
        snake = world.registry.get(snake_id)

        # assert - should start with no tail segments
        assert snake.body.segments == []
        assert snake.body.size == 1
        assert snake.body.alive is True

    def test_create_snake_custom_colors(self):
        """Test snake can be created with custom colors."""
        # arrange
        board = Board(width=400, height=400, cell_size=20)
        world = World(board)
        head_color = (255, 0, 0)  # red
        tail_color = (255, 100, 100)  # light red

        # act
        snake_id = create_snake(
            world, grid_size=20, head_color=head_color, tail_color=tail_color
        )
        snake = world.registry.get(snake_id)

        # assert
        assert snake.palette.primary_color == head_color
        assert snake.palette.secondary_color == tail_color
        assert snake.renderable.color.to_tuple() == head_color

    def test_create_snake_default_colors(self):
        """Test snake uses default colors when not specified."""
        # arrange
        board = Board(width=400, height=400, cell_size=20)
        world = World(board)

        # act
        snake_id = create_snake(world, grid_size=20)
        snake = world.registry.get(snake_id)

        # assert - default green colors
        assert snake.palette.primary_color == (0, 170, 0)
        assert snake.palette.secondary_color == (0, 255, 0)

    def test_create_snake_interpolation(self):
        """Test snake has interpolation component."""
        # arrange
        board = Board(width=400, height=400, cell_size=20)
        world = World(board)

        # act
        snake_id = create_snake(world, grid_size=20)
        snake = world.registry.get(snake_id)

        # assert
        assert snake.interpolation.alpha == 0.0
        assert snake.interpolation.wrapped_axis == "none"

    def test_create_snake_renderable(self):
        """Test snake has correct renderable properties."""
        # arrange
        board = Board(width=400, height=400, cell_size=20)
        world = World(board)
        grid_size = 20

        # act
        snake_id = create_snake(world, grid_size=grid_size)
        snake = world.registry.get(snake_id)

        # assert
        assert snake.renderable.shape == "square"
        assert snake.renderable.size == grid_size


class TestApplePrefab:
    """Test suite for create_apple prefab factory."""

    def test_create_apple_basic(self):
        """Test basic apple creation."""
        # arrange
        board = Board(width=400, height=400, cell_size=20)
        world = World(board)

        # act
        apple_id = create_apple(world, x=100, y=100, grid_size=20)

        # assert
        assert world.registry.has(apple_id)
        apple = world.registry.get(apple_id)
        assert apple is not None
        assert apple.get_type() == EntityType.APPLE

    def test_create_apple_position(self):
        """Test apple is created at correct position."""
        # arrange
        board = Board(width=400, height=400, cell_size=20)
        world = World(board)

        # act
        apple_id = create_apple(world, x=140, y=200, grid_size=20)
        apple = world.registry.get(apple_id)

        # assert
        assert apple.position.x == 140
        assert apple.position.y == 200

    def test_create_apple_edible(self):
        """Test apple has correct edible properties."""
        # arrange
        board = Board(width=400, height=400, cell_size=20)
        world = World(board)

        # act
        apple_id = create_apple(world, x=100, y=100, grid_size=20, points=15, growth=2)
        apple = world.registry.get(apple_id)

        # assert
        assert apple.edible.points == 15
        assert apple.edible.growth == 2

    def test_create_apple_default_edible(self):
        """Test apple uses default edible values."""
        # arrange
        board = Board(width=400, height=400, cell_size=20)
        world = World(board)

        # act
        apple_id = create_apple(world, x=100, y=100, grid_size=20)
        apple = world.registry.get(apple_id)

        # assert
        assert apple.edible.points == 10
        assert apple.edible.growth == 1

    def test_create_apple_custom_color(self):
        """Test apple can be created with custom color."""
        # arrange
        board = Board(width=400, height=400, cell_size=20)
        world = World(board)
        color = (255, 215, 0)  # gold

        # act
        apple_id = create_apple(world, x=100, y=100, grid_size=20, color=color)
        apple = world.registry.get(apple_id)

        # assert
        assert apple.renderable.color.to_tuple() == color

    def test_create_apple_default_color(self):
        """Test apple uses default color when not specified."""
        # arrange
        board = Board(width=400, height=400, cell_size=20)
        world = World(board)

        # act
        apple_id = create_apple(world, x=100, y=100, grid_size=20)
        apple = world.registry.get(apple_id)

        # assert - default red
        assert apple.renderable.color.to_tuple() == (170, 0, 0)

    def test_create_apple_renderable(self):
        """Test apple has correct renderable properties."""
        # arrange
        board = Board(width=400, height=400, cell_size=20)
        world = World(board)
        grid_size = 20

        # act
        apple_id = create_apple(world, x=100, y=100, grid_size=grid_size)
        apple = world.registry.get(apple_id)

        # assert
        assert apple.renderable.shape == "circle"
        assert apple.renderable.size == grid_size

    def test_create_multiple_apples(self):
        """Test creating multiple apples."""
        # arrange
        board = Board(width=400, height=400, cell_size=20)
        world = World(board)

        # act
        apple_id1 = create_apple(world, x=100, y=100, grid_size=20)
        apple_id2 = create_apple(world, x=200, y=200, grid_size=20)
        apple_id3 = create_apple(world, x=300, y=300, grid_size=20)

        # assert - all have unique IDs
        assert apple_id1 != apple_id2
        assert apple_id2 != apple_id3
        assert apple_id1 != apple_id3

        # assert - all exist in registry
        assert world.registry.has(apple_id1)
        assert world.registry.has(apple_id2)
        assert world.registry.has(apple_id3)


class TestObstaclePrefab:
    """Test suite for create_obstacles prefab factory."""

    def test_create_obstacles_none_difficulty(self):
        """Test no obstacles created with 'None' difficulty."""
        # arrange
        board = Board(width=400, height=400, cell_size=20)
        world = World(board)

        # act
        obstacle_ids = create_obstacles(world, "None", grid_size=20)

        # assert
        assert len(obstacle_ids) == 0

    def test_create_obstacles_easy_difficulty(self):
        """Test correct number of obstacles for 'Easy' difficulty."""
        # arrange
        board = Board(width=20, height=20, cell_size=20)  # 20x20 tiles
        world = World(board)
        total_cells = 20 * 20  # 400 tiles
        expected_count = int(total_cells * 0.04)  # 4% = 16

        # act
        obstacle_ids = create_obstacles(world, "Easy", grid_size=20, random_seed=42)

        # assert
        assert len(obstacle_ids) == expected_count

    def test_create_obstacles_medium_difficulty(self):
        """Test correct number of obstacles for 'Medium' difficulty."""
        # arrange
        board = Board(width=20, height=20, cell_size=20)  # 20x20 tiles
        world = World(board)
        total_cells = 20 * 20  # 400 tiles
        expected_count = int(total_cells * 0.06)  # 6% = 24

        # act
        obstacle_ids = create_obstacles(world, "Medium", grid_size=20, random_seed=42)

        # assert
        assert len(obstacle_ids) == expected_count

    def test_create_obstacles_hard_difficulty(self):
        """Test correct number of obstacles for 'Hard' difficulty."""
        # arrange
        board = Board(width=20, height=20, cell_size=20)  # 20x20 tiles
        world = World(board)
        total_cells = 20 * 20  # 400 tiles
        expected_count = int(total_cells * 0.10)  # 10% = 40

        # act
        obstacle_ids = create_obstacles(world, "Hard", grid_size=20, random_seed=42)

        # assert
        assert len(obstacle_ids) == expected_count

    def test_create_obstacles_impossible_difficulty(self):
        """Test correct number of obstacles for 'Impossible' difficulty."""
        # arrange
        board = Board(width=20, height=20, cell_size=20)  # 20x20 tiles
        world = World(board)
        total_cells = 20 * 20  # 400 tiles
        expected_count = int(total_cells * 0.15)  # 15% = 60

        # act
        obstacle_ids = create_obstacles(
            world, "Impossible", grid_size=20, random_seed=42
        )

        # assert
        assert len(obstacle_ids) == expected_count

    def test_create_obstacles_are_valid_entities(self):
        """Test all created obstacles are valid entities."""
        # arrange
        board = Board(width=20, height=20, cell_size=20)  # 20x20 tiles
        world = World(board)

        # act
        obstacle_ids = create_obstacles(world, "Medium", grid_size=20, random_seed=42)

        # assert
        for obstacle_id in obstacle_ids:
            assert world.registry.has(obstacle_id)
            obstacle = world.registry.get(obstacle_id)
            assert obstacle is not None
            assert obstacle.get_type() == EntityType.OBSTACLE

    def test_create_obstacles_positions_are_on_grid(self):
        """Test all obstacles are positioned on grid boundaries."""
        # arrange
        board = Board(width=20, height=20, cell_size=20)  # 20x20 tiles
        world = World(board)
        grid_size = 20

        # act
        obstacle_ids = create_obstacles(
            world, "Medium", grid_size=grid_size, random_seed=42
        )

        # assert
        for obstacle_id in obstacle_ids:
            obstacle = world.registry.get(obstacle_id)
            # positions should be multiples of grid_size
            assert obstacle.position.x % grid_size == 0
            assert obstacle.position.y % grid_size == 0

    def test_create_obstacles_no_duplicates(self):
        """Test no two obstacles occupy the same position."""
        # arrange
        board = Board(width=20, height=20, cell_size=20)  # 20x20 tiles
        world = World(board)

        # act
        obstacle_ids = create_obstacles(world, "Hard", grid_size=20, random_seed=42)

        # assert
        positions = set()
        for obstacle_id in obstacle_ids:
            obstacle = world.registry.get(obstacle_id)
            pos = (obstacle.position.x, obstacle.position.y)
            assert pos not in positions, f"Duplicate position found: {pos}"
            positions.add(pos)

    def test_create_obstacles_avoids_occupied_cells(self):
        """Test obstacles don't spawn on occupied cells."""
        # arrange
        board = Board(width=20, height=20, cell_size=20)  # 20x20 tiles
        world = World(board)

        # create a snake first
        snake_id = create_snake(world, grid_size=20)
        snake = world.registry.get(snake_id)
        snake_pos = (snake.position.x, snake.position.y)

        # act
        obstacle_ids = create_obstacles(world, "Medium", grid_size=20, random_seed=42)

        # assert - no obstacle should be at snake position
        for obstacle_id in obstacle_ids:
            obstacle = world.registry.get(obstacle_id)
            obstacle_pos = (obstacle.position.x, obstacle.position.y)
            assert obstacle_pos != snake_pos

    def test_create_obstacles_deterministic_with_seed(self):
        """Test obstacle placement is deterministic with same seed."""
        # arrange
        board1 = Board(width=20, height=20, cell_size=20)  # 20x20 tiles
        world1 = World(board1)
        board2 = Board(width=20, height=20, cell_size=20)  # 20x20 tiles
        world2 = World(board2)

        # act
        obstacle_ids1 = create_obstacles(
            world1, "Medium", grid_size=20, random_seed=123
        )
        obstacle_ids2 = create_obstacles(
            world2, "Medium", grid_size=20, random_seed=123
        )

        # assert - same positions in same order
        assert len(obstacle_ids1) == len(obstacle_ids2)
        for id1, id2 in zip(obstacle_ids1, obstacle_ids2):
            obs1 = world1.registry.get(id1)
            obs2 = world2.registry.get(id2)
            assert obs1.position.x == obs2.position.x
            assert obs1.position.y == obs2.position.y

    def test_create_obstacles_has_obstacle_tag(self):
        """Test all obstacles have ObstacleTag component."""
        # arrange
        board = Board(width=20, height=20, cell_size=20)  # 20x20 tiles
        world = World(board)

        # act
        obstacle_ids = create_obstacles(world, "Easy", grid_size=20, random_seed=42)

        # assert
        for obstacle_id in obstacle_ids:
            obstacle = world.registry.get(obstacle_id)
            assert hasattr(obstacle, "tag")
            assert obstacle.tag is not None

    def test_create_obstacles_returns_empty_list_on_none(self):
        """Test returns empty list for None difficulty."""
        # arrange
        board = Board(width=20, height=20, cell_size=20)  # 20x20 tiles
        world = World(board)

        # act
        result = create_obstacles(world, "None", grid_size=20)

        # assert
        assert isinstance(result, list)
        assert len(result) == 0
