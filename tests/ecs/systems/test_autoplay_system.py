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

"""Tests for AutoplaySystem."""

import pytest

from ecs.systems.autoplay import AutoplaySystem
from ecs.world import World
from ecs.board import Board
from ecs.entities.snake import Snake
from ecs.entities.apple import Apple
from ecs.entities.obstacle_field import Obstacle
from ecs.components.position import Position
from ecs.components.velocity import Velocity
from ecs.components.snake_body import SnakeBody
from ecs.components.input_buffer import InputBuffer
from ecs.components.edible import Edible
from ecs.components.renderable import Renderable
from ecs.components.interpolation import Interpolation
from ecs.components.obstacle import ObstacleTag
from ecs.components.hunger import Hunger
from core.types.color import Color
from game.game_modes_registry import AUTOPLAY_MODE_NAME, CLASSIC_MODE_NAME


@pytest.fixture
def world():
    """Create a test world."""
    board = Board(10, 10)
    return World(board)


@pytest.fixture
def snake(world):
    """Create a snake entity."""
    snake = Snake(
        position=Position(5, 5),
        velocity=Velocity(1, 0),
        body=SnakeBody(
            size=3, segments=[Position(5, 5), Position(4, 5), Position(3, 5)]
        ),
        interpolation=Interpolation(),
        renderable=Renderable(shape="square", color=Color(0, 255, 0)),
        input_buffer=InputBuffer(),
        hunger=(Hunger(current_time=0.0, max_time=0.0)),
    )
    world.registry.add(snake)
    return snake


@pytest.fixture
def apple(world):
    """Create an apple entity."""
    apple = Apple(
        position=Position(8, 5),
        edible=Edible(10, 1),
        renderable=Renderable(shape="circle", color=Color(255, 0, 0)),
    )
    world.registry.add(apple)
    return apple


def test_autoplay_inactive_in_classic_mode(world, snake, apple):
    """Test that AutoplaySystem does nothing in classic mode."""
    system = AutoplaySystem(CLASSIC_MODE_NAME)
    world.set_dt_ms(100)

    system.update(world)

    assert len(snake.input_buffer.moves) == 0


def test_autoplay_moves_towards_apple(world, snake, apple):
    """Test that AutoplaySystem moves snake towards apple."""
    system = AutoplaySystem(AUTOPLAY_MODE_NAME)
    world.set_dt_ms(100)

    system.update(world)

    assert len(snake.input_buffer.moves) > 0
    # Apple is at (8, 5), snake at (5, 5) facing right (1, 0).
    # Should continue moving right.
    dx, dy = snake.input_buffer.moves[0]
    assert dx == 1
    assert dy == 0


def test_autoplay_avoids_obstacles(world, snake, apple):
    """Test that AutoplaySystem avoids obstacles."""
    # Place obstacle in front of snake
    obstacle = Obstacle(
        position=Position(6, 5),
        tag=ObstacleTag(),
        renderable=Renderable(shape="square", color=Color(128, 128, 128)),
    )
    world.registry.add(obstacle)

    system = AutoplaySystem(AUTOPLAY_MODE_NAME)
    world.set_dt_ms(100)

    system.update(world)

    assert len(snake.input_buffer.moves) > 0
    dx, dy = snake.input_buffer.moves[0]
    # Should turn up or down, not go right (1, 0)
    assert (dx, dy) != (1, 0)
    assert (dx, dy) in [(0, 1), (0, -1)]
