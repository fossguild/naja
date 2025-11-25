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

"""Cheese mode mechanics verification tests."""

from ecs.world import World
from ecs.board import Board
from ecs.systems.collision import CollisionSystem
from ecs.systems.movement import MovementSystem
from ecs.entities.snake import Snake
from ecs.components.position import Position
from ecs.components.velocity import Velocity
from ecs.components.snake_body import SnakeBody
from ecs.components.game_state import GameState
from ecs.components.interpolation import Interpolation
from ecs.components.renderable import Renderable
from ecs.components.input_buffer import InputBuffer
from core.types.color import Color


def create_world_with_snake(cheese_mode=True):
    """Create a world with a snake for testing.

    Args:
        cheese_mode: Whether Cheese mode is enabled

    Returns:
        tuple: (World, Snake entity)
    """
    board = Board(width=20, height=20, cell_size=10)
    world = World(board)

    # Game State
    class GameStateEntity:
        def __init__(self):
            self.game_state = GameState(cheese_mode_enabled=cheese_mode)

        def get_type(self):
            return None

    world.registry.add(GameStateEntity())

    # Snake
    snake = Snake(
        position=Position(x=5, y=5),
        velocity=Velocity(dx=1, dy=0),
        body=SnakeBody(segments=[], size=1),
        interpolation=Interpolation(),
        input_buffer=InputBuffer(),
        renderable=Renderable(shape="square", color=Color(0, 255, 0), size=10),
    )
    world.registry.add(snake)
    return world, snake


def test_segment_parity():
    """Verify segment parity: Index 0=Solid, 1=Hole, etc."""
    world, snake = create_world_with_snake(cheese_mode=True)
    movement = MovementSystem()

    # Grow snake to have multiple segments
    # Head at (5,5). Moving Right (dx=1).
    # We need to simulate movement to generate segments

    # Initial: Head(5,5), Segments=[]
    # Set size to 2 so we get 1 tail segment
    snake.body.size = 2

    # Move 1: Head(6,5), Segments=[(5,5)] (Index 0 - Solid)
    world.set_dt_ms(1000)
    movement.update(world)
    assert len(snake.body.segments) == 1
    assert snake.body.segments[0].x == 5
    assert snake.body.segments[0].y == 5

    # Move 2: Head(7,5), Segments=[(6,5), (5,5)]?
    # Wait, size is 1. So it will only keep 1 segment?
    # desired_tail_len = size - 1. If size=1, len=0.
    # So we need to increase size.

    snake.body.size = 5  # Head + 4 segments

    # Move multiple times to fill body
    for _ in range(5):
        movement.update(world)

    # Now snake should have 4 segments
    assert len(snake.body.segments) == 4

    # Head started at 5.
    # Move 1: Head -> 6
    # Loop 5 times: Head -> 7, 8, 9, 10, 11
    # Current Head is at (11, 5)

    # Segments should be trailing:
    # Seg 0: (10,5) - Solid
    # Seg 1: (9,5) - Hole
    # Seg 2: (8,5) - Solid
    # Seg 3: (7,5) - Hole

    assert snake.body.segments[0].x == 10  # Closest to head
    assert snake.body.segments[1].x == 9
    assert snake.body.segments[2].x == 8
    assert snake.body.segments[3].x == 7

    # Parity check is implicit in logic, but let's verify collision logic respects this
    collision = CollisionSystem()

    # Test Collision with Seg 0 (Solid)
    # Move head to (10,5) - Impossible in game, but manually set for test
    snake.position.x = 10
    snake.position.y = 5
    # Ensure no accidental tunneling with other segments
    snake.position.prev_x = 10
    snake.position.prev_y = 5
    assert collision._check_self_bite(world), "Should collide with Seg 0 (Solid)"

    # Test Collision with Seg 1 (Hole)
    snake.position.x = 9
    snake.position.y = 5
    snake.position.prev_x = 9
    snake.position.prev_y = 5
    assert not collision._check_self_bite(world), "Should NOT collide with Seg 1 (Hole)"

    # Test Collision with Seg 2 (Solid)
    snake.position.x = 8
    snake.position.y = 5
    snake.position.prev_x = 8
    snake.position.prev_y = 5
    assert collision._check_self_bite(world), "Should collide with Seg 2 (Solid)"

    # Test Collision with Seg 3 (Hole)
    snake.position.x = 7
    snake.position.y = 5
    snake.position.prev_x = 7
    snake.position.prev_y = 5
    assert not collision._check_self_bite(world), "Should NOT collide with Seg 3 (Hole)"


def test_tunneling_fix():
    """Verify CCD prevents tunneling through solid segments."""
    world, snake = create_world_with_snake(cheese_mode=True)
    collision = CollisionSystem()

    # Setup a swap scenario with Seg 0 (Solid)
    # Head at (5,5). Seg 0 at (6,5).
    snake.position.x = 6  # Current Head
    snake.position.y = 5
    snake.position.prev_x = 5  # Prev Head
    snake.position.prev_y = 5

    snake.body.segments = [
        Position(x=5, y=5, prev_x=6, prev_y=5)
    ]  # Seg 0: Current(5,5), Prev(6,5)

    # This represents a swap: Head 5->6, Seg 6->5
    assert collision._check_self_bite(
        world
    ), "Should detect tunneling with Solid segment"

    # Setup a swap scenario with Seg 1 (Hole)
    # Head at (5,5). Seg 1 at (6,5).
    snake.body.segments = [
        Position(x=0, y=0),  # Seg 0 (Solid) - far away
        Position(x=5, y=5, prev_x=6, prev_y=5),  # Seg 1 (Hole) - swapping
    ]

    assert not collision._check_self_bite(
        world
    ), "Should IGNORE tunneling with Hole segment"
