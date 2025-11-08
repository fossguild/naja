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

"""Grape entity prefab factory."""

from typing import Optional

from src.ecs.world import World
from src.ecs.entities.apple import Apple
from src.ecs.components.position import Position
from src.ecs.components.edible import Edible
from src.ecs.components.renderable import Renderable
from src.core.types.color import Color


def create_grape(
    world: World,
    x: int,
    y: int,
    grid_size: int,
    color: Optional[tuple[int, int, int]] = None,
) -> int:
    """Create a grape entity at the specified position.

    Grapes grow snake by 1 segment and decrease speed by 20% for strategic control.

    Args:
        world: ECS world to create entity in
        x: X position in pixels (grid-aligned)
        y: Y position in pixels (grid-aligned)
        grid_size: Size of each grid cell in pixels
        color: RGB color for grape (default: purple)

    Returns:
        int: Entity ID of created grape

    Example:
        >>> grape_id = create_grape(world, x=100, y=100, grid_size=20)
        >>> grape = world.registry.get(grape_id)
        >>> grape.edible.speed_modifier
        0.8
    """
    # default color if not specified
    if color is None:
        color = (128, 0, 128)  # purple

    # create grape entity with required components
    # using Apple class as base (all fruits share same structure)
    grape = Apple(
        position=Position(x=x, y=y, prev_x=x, prev_y=y),
        edible=Edible(
            points=10,
            growth=1,
            speed_modifier=0.8,  # slows down by 20%
        ),
        renderable=Renderable(
            shape="circle",
            color=Color(color[0], color[1], color[2]),
            size=grid_size,
        ),
    )

    # register entity with world and return ID
    entity_id = world.registry.add(grape)
    return entity_id
