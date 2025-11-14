#!/usr/bin/env python3
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

"""Snake entity prefab factory."""

from typing import Optional

from ecs.world import World
from ecs.entities.snake import Snake
from ecs.components.position import Position
from ecs.components.velocity import Velocity
from ecs.components.snake_body import SnakeBody
from ecs.components.interpolation import Interpolation
from ecs.components.renderable import Renderable
from core.types.color import Color


def create_snake(
    world: World,
    grid_size: int,
    initial_speed: float = 4.0,
    head_color: Optional[tuple[int, int, int]] = None,
    tail_color: Optional[tuple[int, int, int]] = None,
) -> int:
    """Create a snake entity with all required components.

    Args:
        world: ECS world to create entity in
        grid_size: Size of each grid cell in pixels
        initial_speed: Initial movement speed in cells per second
        head_color: RGB color for snake head (default: green)
        tail_color: RGB color for snake tail (default: light green)

    Returns:
        int: Entity ID of created snake

    Example:
        >>> snake_id = create_snake(world, grid_size=20)
        >>> snake = world.registry.get(snake_id)
        >>> snake.position.x, snake.position.y
        (20, 20)
    """
    # default colors if not specified
    if head_color is None:
        head_color = (0, 170, 0)  # dark green
    if tail_color is None:
        tail_color = (0, 255, 0)  # light green

    # starting position in GRID COORDINATES (not pixels)
    # board center
    start_x = world.board.width // 2
    start_y = world.board.height // 2

    # create snake entity with all required components
    snake = Snake(
        position=Position(x=start_x, y=start_y, prev_x=start_x, prev_y=start_y),
        velocity=Velocity(dx=1, dy=0, speed=initial_speed),
        body=SnakeBody(segments=[], size=1, alive=True),
        interpolation=Interpolation(alpha=0.0, wrapped_axis="none"),
        renderable=Renderable(
            shape="square",
            color=Color(head_color[0], head_color[1], head_color[2]),
            secondary_color=Color(tail_color[0], tail_color[1], tail_color[2]),
            size=grid_size,
        ),
    )

    # register entity with world and return ID
    entity_id = world.registry.add(snake)
    return entity_id
