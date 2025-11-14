#!/usr/bin/env python3
#
#
#   Copyright (c) 2023, Monaco F. J. <monaco@usp.br>
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

"""Apple entity prefab factory."""

from typing import Optional

from ecs.world import World
from ecs.entities.apple import Apple
from ecs.components.position import Position
from ecs.components.edible import Edible
from ecs.components.renderable import Renderable
from core.types.color import Color


def create_apple(
    world: World,
    x: int,
    y: int,
    grid_size: int,
    color: Optional[tuple[int, int, int]] = None,
    points: int = 10,
    growth: int = 1,
) -> int:
    """Create an apple entity at the specified position.

    Args:
        world: ECS world to create entity in
        x: X position in pixels (grid-aligned)
        y: Y position in pixels (grid-aligned)
        grid_size: Size of each grid cell in pixels
        color: RGB color for apple (default: red)
        points: Points awarded when eaten
        growth: Number of segments to add to snake when eaten

    Returns:
        int: Entity ID of created apple

    Example:
        >>> apple_id = create_apple(world, x=100, y=100, grid_size=20)
        >>> apple = world.registry.get(apple_id)
        >>> apple.position.x, apple.position.y
        (100, 100)
    """
    # default color if not specified
    if color is None:
        color = (170, 0, 0)  # red

    # create apple entity with required components
    apple = Apple(
        position=Position(x=x, y=y, prev_x=x, prev_y=y),
        edible=Edible(points=points, growth=growth),
        renderable=Renderable(
            shape="circle",
            color=Color(color[0], color[1], color[2]),
            size=grid_size,
        ),
    )

    # register entity with world and return ID
    entity_id = world.registry.add(apple)
    return entity_id
