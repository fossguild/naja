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

"""Tests for CollisionSystem."""

import pytest
from unittest.mock import Mock

from src.ecs.systems.collision import CollisionSystem
from src.ecs.world import World
from src.ecs.board import Board


@pytest.fixture
def world():
    """Create a test world."""
    board = Board(20, 20)
    return World(board)


@pytest.fixture
def mock_callbacks():
    """Create mock callback functions."""
    return {
        "get_snake_head_position": Mock(return_value=(100, 100)),
        "get_snake_tail_positions": Mock(return_value=[]),
        "get_snake_next_position": Mock(return_value=(120, 100)),
        "get_electric_walls": Mock(return_value=True),
        "get_grid_dimensions": Mock(return_value=(800, 600, 20)),
        "get_current_speed": Mock(return_value=5.0),
        "get_max_speed": Mock(return_value=20.0),
        "death": Mock(),
        "apple_eaten": Mock(),
        "speed_increase": Mock(),
    }


def test_collision_system_creation(mock_callbacks):
    """Test that CollisionSystem can be created with all callbacks."""
    system = CollisionSystem(
        get_snake_head_position=mock_callbacks["get_snake_head_position"],
        get_snake_tail_positions=mock_callbacks["get_snake_tail_positions"],
        get_snake_next_position=mock_callbacks["get_snake_next_position"],
        get_electric_walls=mock_callbacks["get_electric_walls"],
        get_grid_dimensions=mock_callbacks["get_grid_dimensions"],
        get_current_speed=mock_callbacks["get_current_speed"],
        get_max_speed=mock_callbacks["get_max_speed"],
        death_callback=mock_callbacks["death"],
        apple_eaten_callback=mock_callbacks["apple_eaten"],
        speed_increase_callback=mock_callbacks["speed_increase"],
    )

    assert system is not None


# Wall Collision Tests


def test_collision_system_detects_wall_collision_electric_mode(world, mock_callbacks):
    """Test that CollisionSystem detects wall collision in electric mode."""
    # snake trying to go out of bounds
    mock_callbacks["get_snake_next_position"].return_value = (-20, 100)
    mock_callbacks["get_electric_walls"].return_value = True
    mock_callbacks["get_grid_dimensions"].return_value = (800, 600, 20)

    system = CollisionSystem(
        get_snake_next_position=mock_callbacks["get_snake_next_position"],
        get_electric_walls=mock_callbacks["get_electric_walls"],
        get_grid_dimensions=mock_callbacks["get_grid_dimensions"],
        death_callback=mock_callbacks["death"],
    )

    system.update(world)

    # death callback should be called with "wall"
    mock_callbacks["death"].assert_called_once_with("wall")


def test_collision_system_allows_wrapping_non_electric_mode(world, mock_callbacks):
    """Test that CollisionSystem allows going out of bounds in wrapping mode."""
    # snake trying to go out of bounds
    mock_callbacks["get_snake_next_position"].return_value = (-20, 100)
    mock_callbacks["get_electric_walls"].return_value = False  # wrapping mode
    mock_callbacks["get_grid_dimensions"].return_value = (800, 600, 20)
    mock_callbacks["get_snake_tail_positions"].return_value = []

    system = CollisionSystem(
        get_snake_next_position=mock_callbacks["get_snake_next_position"],
        get_electric_walls=mock_callbacks["get_electric_walls"],
        get_grid_dimensions=mock_callbacks["get_grid_dimensions"],
        get_snake_tail_positions=mock_callbacks["get_snake_tail_positions"],
        death_callback=mock_callbacks["death"],
    )

    system.update(world)

    # death callback should NOT be called (wrapping is allowed)
    mock_callbacks["death"].assert_not_called()


def test_collision_system_detects_wall_collision_right_edge(world, mock_callbacks):
    """Test wall collision on right edge."""
    mock_callbacks["get_snake_next_position"].return_value = (800, 100)  # out of bounds
    mock_callbacks["get_electric_walls"].return_value = True
    mock_callbacks["get_grid_dimensions"].return_value = (800, 600, 20)

    system = CollisionSystem(
        get_snake_next_position=mock_callbacks["get_snake_next_position"],
        get_electric_walls=mock_callbacks["get_electric_walls"],
        get_grid_dimensions=mock_callbacks["get_grid_dimensions"],
        death_callback=mock_callbacks["death"],
    )

    system.update(world)

    mock_callbacks["death"].assert_called_once_with("wall")


def test_collision_system_detects_wall_collision_bottom_edge(world, mock_callbacks):
    """Test wall collision on bottom edge."""
    mock_callbacks["get_snake_next_position"].return_value = (100, 600)  # out of bounds
    mock_callbacks["get_electric_walls"].return_value = True
    mock_callbacks["get_grid_dimensions"].return_value = (800, 600, 20)

    system = CollisionSystem(
        get_snake_next_position=mock_callbacks["get_snake_next_position"],
        get_electric_walls=mock_callbacks["get_electric_walls"],
        get_grid_dimensions=mock_callbacks["get_grid_dimensions"],
        death_callback=mock_callbacks["death"],
    )

    system.update(world)

    mock_callbacks["death"].assert_called_once_with("wall")


# Self-Bite Tests


def test_collision_system_detects_self_bite(world, mock_callbacks):
    """Test that CollisionSystem detects self-bite collision."""
    # snake head moving into tail segment
    mock_callbacks["get_snake_next_position"].return_value = (140, 100)
    mock_callbacks["get_snake_tail_positions"].return_value = [
        (120, 100),
        (140, 100),  # collision here!
        (160, 100),
    ]
    mock_callbacks["get_electric_walls"].return_value = False
    mock_callbacks["get_grid_dimensions"].return_value = (800, 600, 20)

    system = CollisionSystem(
        get_snake_next_position=mock_callbacks["get_snake_next_position"],
        get_snake_tail_positions=mock_callbacks["get_snake_tail_positions"],
        get_electric_walls=mock_callbacks["get_electric_walls"],
        get_grid_dimensions=mock_callbacks["get_grid_dimensions"],
        death_callback=mock_callbacks["death"],
    )

    system.update(world)

    mock_callbacks["death"].assert_called_once_with("self_bite")


def test_collision_system_no_false_positive_self_bite(world, mock_callbacks):
    """Test that CollisionSystem doesn't detect false positive self-bite."""
    # snake head NOT colliding with tail
    mock_callbacks["get_snake_next_position"].return_value = (200, 100)
    mock_callbacks["get_snake_tail_positions"].return_value = [
        (120, 100),
        (140, 100),
        (160, 100),
    ]
    mock_callbacks["get_electric_walls"].return_value = False
    mock_callbacks["get_grid_dimensions"].return_value = (800, 600, 20)

    system = CollisionSystem(
        get_snake_next_position=mock_callbacks["get_snake_next_position"],
        get_snake_tail_positions=mock_callbacks["get_snake_tail_positions"],
        get_electric_walls=mock_callbacks["get_electric_walls"],
        get_grid_dimensions=mock_callbacks["get_grid_dimensions"],
        death_callback=mock_callbacks["death"],
    )

    system.update(world)

    # no death should occur
    mock_callbacks["death"].assert_not_called()


def test_collision_system_allows_empty_tail(world, mock_callbacks):
    """Test that CollisionSystem handles empty tail (no self-bite possible)."""
    mock_callbacks["get_snake_next_position"].return_value = (120, 100)
    mock_callbacks["get_snake_tail_positions"].return_value = []  # no tail yet
    mock_callbacks["get_electric_walls"].return_value = False
    mock_callbacks["get_grid_dimensions"].return_value = (800, 600, 20)

    system = CollisionSystem(
        get_snake_next_position=mock_callbacks["get_snake_next_position"],
        get_snake_tail_positions=mock_callbacks["get_snake_tail_positions"],
        get_electric_walls=mock_callbacks["get_electric_walls"],
        get_grid_dimensions=mock_callbacks["get_grid_dimensions"],
        death_callback=mock_callbacks["death"],
    )

    system.update(world)

    mock_callbacks["death"].assert_not_called()


# Obstacle Collision Tests


def test_collision_system_detects_obstacle_collision(world, mock_callbacks):
    """Test that CollisionSystem detects obstacle collision."""
    # add obstacle to world at position (140, 100)
    from old_code.entities import Obstacle

    obstacle = Obstacle(140, 100, None, 20)
    world.registry.add(obstacle)

    # snake moving into obstacle
    mock_callbacks["get_snake_next_position"].return_value = (140, 100)
    mock_callbacks["get_snake_tail_positions"].return_value = []
    mock_callbacks["get_electric_walls"].return_value = False
    mock_callbacks["get_grid_dimensions"].return_value = (800, 600, 20)

    system = CollisionSystem(
        get_snake_next_position=mock_callbacks["get_snake_next_position"],
        get_snake_tail_positions=mock_callbacks["get_snake_tail_positions"],
        get_electric_walls=mock_callbacks["get_electric_walls"],
        get_grid_dimensions=mock_callbacks["get_grid_dimensions"],
        death_callback=mock_callbacks["death"],
    )

    system.update(world)

    mock_callbacks["death"].assert_called_once_with("obstacle")


def test_collision_system_no_false_positive_obstacle(world, mock_callbacks):
    """Test that CollisionSystem doesn't detect false positive obstacle."""
    # add obstacle to world at position (140, 100)
    from old_code.entities import Obstacle

    obstacle = Obstacle(140, 100, None, 20)
    world.registry.add(obstacle)

    # snake NOT moving into obstacle
    mock_callbacks["get_snake_next_position"].return_value = (200, 100)
    mock_callbacks["get_snake_tail_positions"].return_value = []
    mock_callbacks["get_electric_walls"].return_value = False
    mock_callbacks["get_grid_dimensions"].return_value = (800, 600, 20)

    system = CollisionSystem(
        get_snake_next_position=mock_callbacks["get_snake_next_position"],
        get_snake_tail_positions=mock_callbacks["get_snake_tail_positions"],
        get_electric_walls=mock_callbacks["get_electric_walls"],
        get_grid_dimensions=mock_callbacks["get_grid_dimensions"],
        death_callback=mock_callbacks["death"],
    )

    system.update(world)

    mock_callbacks["death"].assert_not_called()


def test_collision_system_handles_multiple_obstacles(world, mock_callbacks):
    """Test CollisionSystem with multiple obstacles."""
    # add multiple obstacles
    from old_code.entities import Obstacle

    world.registry.add(Obstacle(140, 100, None, 20))
    world.registry.add(Obstacle(160, 100, None, 20))
    world.registry.add(Obstacle(180, 100, None, 20))

    # snake moving into one of them
    mock_callbacks["get_snake_next_position"].return_value = (160, 100)
    mock_callbacks["get_snake_tail_positions"].return_value = []
    mock_callbacks["get_electric_walls"].return_value = False
    mock_callbacks["get_grid_dimensions"].return_value = (800, 600, 20)

    system = CollisionSystem(
        get_snake_next_position=mock_callbacks["get_snake_next_position"],
        get_snake_tail_positions=mock_callbacks["get_snake_tail_positions"],
        get_electric_walls=mock_callbacks["get_electric_walls"],
        get_grid_dimensions=mock_callbacks["get_grid_dimensions"],
        death_callback=mock_callbacks["death"],
    )

    system.update(world)

    mock_callbacks["death"].assert_called_once_with("obstacle")


# Apple Collision Tests


def test_collision_system_detects_apple_collision(world, mock_callbacks):
    """Test that CollisionSystem detects apple collision."""
    # add apple to world at position (100, 100)
    from old_code.entities import Apple

    apple = Apple(800, 600, 20)
    apple.x = 100
    apple.y = 100
    world.registry.add(apple)

    # snake head at same position
    mock_callbacks["get_snake_head_position"].return_value = (100, 100)
    mock_callbacks["get_snake_next_position"].return_value = (120, 100)
    mock_callbacks["get_snake_tail_positions"].return_value = []
    mock_callbacks["get_electric_walls"].return_value = False
    mock_callbacks["get_grid_dimensions"].return_value = (800, 600, 20)

    system = CollisionSystem(
        get_snake_head_position=mock_callbacks["get_snake_head_position"],
        get_snake_next_position=mock_callbacks["get_snake_next_position"],
        get_snake_tail_positions=mock_callbacks["get_snake_tail_positions"],
        get_electric_walls=mock_callbacks["get_electric_walls"],
        get_grid_dimensions=mock_callbacks["get_grid_dimensions"],
        apple_eaten_callback=mock_callbacks["apple_eaten"],
    )

    system.update(world)

    # apple_eaten callback should be called
    mock_callbacks["apple_eaten"].assert_called_once()


def test_collision_system_calls_speed_increase(world, mock_callbacks):
    """Test that CollisionSystem calls speed increase callback."""
    # add apple to world
    from old_code.entities import Apple

    apple = Apple(800, 600, 20)
    apple.x = 100
    apple.y = 100
    world.registry.add(apple)

    mock_callbacks["get_snake_head_position"].return_value = (100, 100)
    mock_callbacks["get_snake_next_position"].return_value = (120, 100)
    mock_callbacks["get_snake_tail_positions"].return_value = []
    mock_callbacks["get_electric_walls"].return_value = False
    mock_callbacks["get_grid_dimensions"].return_value = (800, 600, 20)
    mock_callbacks["get_current_speed"].return_value = 10.0
    mock_callbacks["get_max_speed"].return_value = 20.0

    system = CollisionSystem(
        get_snake_head_position=mock_callbacks["get_snake_head_position"],
        get_snake_next_position=mock_callbacks["get_snake_next_position"],
        get_snake_tail_positions=mock_callbacks["get_snake_tail_positions"],
        get_electric_walls=mock_callbacks["get_electric_walls"],
        get_grid_dimensions=mock_callbacks["get_grid_dimensions"],
        get_current_speed=mock_callbacks["get_current_speed"],
        get_max_speed=mock_callbacks["get_max_speed"],
        apple_eaten_callback=mock_callbacks["apple_eaten"],
        speed_increase_callback=mock_callbacks["speed_increase"],
    )

    system.update(world)

    # speed should increase by 10% (10.0 * 1.1 = 11.0)
    mock_callbacks["speed_increase"].assert_called_once_with(11.0)


def test_collision_system_respects_max_speed(world, mock_callbacks):
    """Test that CollisionSystem respects maximum speed limit."""
    # add apple to world
    from old_code.entities import Apple

    apple = Apple(800, 600, 20)
    apple.x = 100
    apple.y = 100
    world.registry.add(apple)

    mock_callbacks["get_snake_head_position"].return_value = (100, 100)
    mock_callbacks["get_snake_next_position"].return_value = (120, 100)
    mock_callbacks["get_snake_tail_positions"].return_value = []
    mock_callbacks["get_electric_walls"].return_value = False
    mock_callbacks["get_grid_dimensions"].return_value = (800, 600, 20)
    mock_callbacks["get_current_speed"].return_value = 19.0  # close to max
    mock_callbacks["get_max_speed"].return_value = 20.0

    system = CollisionSystem(
        get_snake_head_position=mock_callbacks["get_snake_head_position"],
        get_snake_next_position=mock_callbacks["get_snake_next_position"],
        get_snake_tail_positions=mock_callbacks["get_snake_tail_positions"],
        get_electric_walls=mock_callbacks["get_electric_walls"],
        get_grid_dimensions=mock_callbacks["get_grid_dimensions"],
        get_current_speed=mock_callbacks["get_current_speed"],
        get_max_speed=mock_callbacks["get_max_speed"],
        apple_eaten_callback=mock_callbacks["apple_eaten"],
        speed_increase_callback=mock_callbacks["speed_increase"],
    )

    system.update(world)

    # speed should be capped at max_speed (19.0 * 1.1 = 20.9, but capped to 20.0)
    mock_callbacks["speed_increase"].assert_called_once_with(20.0)


def test_collision_system_only_eats_one_apple_per_frame(world, mock_callbacks):
    """Test that CollisionSystem only eats one apple per frame."""
    # add multiple apples at same position (edge case)
    from old_code.entities import Apple

    apple1 = Apple(800, 600, 20)
    apple1.x = 100
    apple1.y = 100
    world.registry.add(apple1)

    apple2 = Apple(800, 600, 20)
    apple2.x = 100
    apple2.y = 100
    world.registry.add(apple2)

    mock_callbacks["get_snake_head_position"].return_value = (100, 100)
    mock_callbacks["get_snake_next_position"].return_value = (120, 100)
    mock_callbacks["get_snake_tail_positions"].return_value = []
    mock_callbacks["get_electric_walls"].return_value = False
    mock_callbacks["get_grid_dimensions"].return_value = (800, 600, 20)

    system = CollisionSystem(
        get_snake_head_position=mock_callbacks["get_snake_head_position"],
        get_snake_next_position=mock_callbacks["get_snake_next_position"],
        get_snake_tail_positions=mock_callbacks["get_snake_tail_positions"],
        get_electric_walls=mock_callbacks["get_electric_walls"],
        get_grid_dimensions=mock_callbacks["get_grid_dimensions"],
        apple_eaten_callback=mock_callbacks["apple_eaten"],
    )

    system.update(world)

    # apple_eaten should only be called once (break after first)
    assert mock_callbacks["apple_eaten"].call_count == 1


# Order and Edge Case Tests


def test_collision_system_checks_fatal_before_apple(world, mock_callbacks):
    """Test that fatal collisions are checked before apple collision."""
    # add apple at position where snake will hit wall
    from old_code.entities import Apple

    apple = Apple(800, 600, 20)
    apple.x = -20  # out of bounds
    apple.y = 100
    world.registry.add(apple)

    # snake head at same position as apple (but also out of bounds)
    mock_callbacks["get_snake_head_position"].return_value = (-20, 100)
    mock_callbacks["get_snake_next_position"].return_value = (-20, 100)
    mock_callbacks["get_electric_walls"].return_value = True
    mock_callbacks["get_grid_dimensions"].return_value = (800, 600, 20)

    system = CollisionSystem(
        get_snake_head_position=mock_callbacks["get_snake_head_position"],
        get_snake_next_position=mock_callbacks["get_snake_next_position"],
        get_electric_walls=mock_callbacks["get_electric_walls"],
        get_grid_dimensions=mock_callbacks["get_grid_dimensions"],
        death_callback=mock_callbacks["death"],
        apple_eaten_callback=mock_callbacks["apple_eaten"],
    )

    system.update(world)

    # death should be called (wall collision)
    mock_callbacks["death"].assert_called_once_with("wall")
    # apple_eaten should NOT be called (died first)
    mock_callbacks["apple_eaten"].assert_not_called()


def test_collision_system_stops_after_death(world, mock_callbacks):
    """Test that CollisionSystem stops checking after death."""
    # setup self-bite scenario
    mock_callbacks["get_snake_next_position"].return_value = (140, 100)
    mock_callbacks["get_snake_tail_positions"].return_value = [(140, 100)]
    mock_callbacks["get_electric_walls"].return_value = False
    mock_callbacks["get_grid_dimensions"].return_value = (800, 600, 20)

    # add apple (should not be checked after death)
    from old_code.entities import Apple

    apple = Apple(800, 600, 20)
    apple.x = 140
    apple.y = 100
    world.registry.add(apple)

    mock_callbacks["get_snake_head_position"].return_value = (140, 100)

    system = CollisionSystem(
        get_snake_head_position=mock_callbacks["get_snake_head_position"],
        get_snake_next_position=mock_callbacks["get_snake_next_position"],
        get_snake_tail_positions=mock_callbacks["get_snake_tail_positions"],
        get_electric_walls=mock_callbacks["get_electric_walls"],
        get_grid_dimensions=mock_callbacks["get_grid_dimensions"],
        death_callback=mock_callbacks["death"],
        apple_eaten_callback=mock_callbacks["apple_eaten"],
    )

    system.update(world)

    # death should be called
    mock_callbacks["death"].assert_called_once_with("self_bite")
    # apple should NOT be checked
    mock_callbacks["apple_eaten"].assert_not_called()


def test_collision_system_with_no_callbacks(world):
    """Test that CollisionSystem handles missing callbacks gracefully."""
    system = CollisionSystem()

    # should not raise any errors
    system.update(world)


def test_collision_system_handles_empty_world(mock_callbacks):
    """Test that CollisionSystem handles empty world (no obstacles, no apples)."""
    empty_world = World(Board(20, 20))

    mock_callbacks["get_snake_head_position"].return_value = (100, 100)
    mock_callbacks["get_snake_next_position"].return_value = (120, 100)
    mock_callbacks["get_snake_tail_positions"].return_value = []
    mock_callbacks["get_electric_walls"].return_value = False
    mock_callbacks["get_grid_dimensions"].return_value = (800, 600, 20)

    system = CollisionSystem(
        get_snake_head_position=mock_callbacks["get_snake_head_position"],
        get_snake_next_position=mock_callbacks["get_snake_next_position"],
        get_snake_tail_positions=mock_callbacks["get_snake_tail_positions"],
        get_electric_walls=mock_callbacks["get_electric_walls"],
        get_grid_dimensions=mock_callbacks["get_grid_dimensions"],
        death_callback=mock_callbacks["death"],
        apple_eaten_callback=mock_callbacks["apple_eaten"],
    )

    system.update(empty_world)

    # no collisions should occur
    mock_callbacks["death"].assert_not_called()
    mock_callbacks["apple_eaten"].assert_not_called()
