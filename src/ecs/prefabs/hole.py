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

"""Hole entity prefab factory."""

from typing import Optional

from ecs.world import World
from ecs.entities.hole import Hole
from ecs.components.position import Position
from ecs.components.hole import Hole as HoleComponent
from ecs.components.renderable import Renderable
from core.types.color import Color


def create_hole(
    world: World,
    x: int,
    y: int,
    grid_size: int,
    color: Optional[tuple[int, int, int]] = None,
) -> int:
    """Create a hole entity at the specified position.

    Args:
        world: ECS world to create entity in
        x: X position in pixels (grid-aligned)
        y: Y position in pixels (grid-aligned)
        grid_size: Size of each grid cell in pixels
        color: RGB color for hole (default: dark gray)

    Returns:
        int: Entity ID of created hole

    Example:
        >>> hole_id = create_hole(world, x=100, y=100, grid_size=20)
        >>> hole = world.registry.get(hole_id)
        >>> hole.position.x, hole.position.y
        (100, 100)
    """
    # default color if not specified
    if color is None:
        color = (50, 50, 50)  # dark gray

    # create hole entity with required components
    hole = Hole(
        position=Position(x=x, y=y, prev_x=x, prev_y=y),
        hole=HoleComponent(),
        renderable=Renderable(
            shape="circle",
            color=Color(color[0], color[1], color[2]),
            size=grid_size,
        ),
    )

    # register entity with world and return ID
    entity_id = world.registry.add(hole)
    return entity_id

