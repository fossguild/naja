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

"""Poisoned apple entity prefab factory."""

from typing import Optional

from src.ecs.world import World
from src.ecs.entities.apple import Apple
from src.ecs.components.position import Position
from src.ecs.components.edible import Edible
from src.ecs.components.poisoned import Poisoned
from src.ecs.components.renderable import Renderable
from src.core.types.color import Color


def create_poisoned_apple(
    world: World,
    x: int,
    y: int,
    grid_size: int,
    color: Optional[tuple[int, int, int]] = None,
) -> int:
    """Create a poisoned apple entity at the specified position.

    Poisoned apples are deadly - eating them ends the game immediately.
    They appear as dark purple/black apples.

    Args:
        world: ECS world to create entity in
        x: X position in pixels (grid-aligned)
        y: Y position in pixels (grid-aligned)
        grid_size: Size of each grid cell in pixels
        color: RGB color for poisoned apple (default: dark purple)

    Returns:
        int: Entity ID of created poisoned apple

    Example:
        >>> poisoned_id = create_poisoned_apple(world, x=100, y=100, grid_size=20)
        >>> poisoned = world.registry.get(poisoned_id)
        >>> poisoned.poisoned.deadly
        True
    """
    # default color if not specified - dark purple/black
    if color is None:
        color = (75, 0, 130)  # dark purple (indigo)

    # create poisoned apple entity with required components
    # using Apple class as base (all apples share same structure)
    poisoned_apple = Apple(
        position=Position(x=x, y=y, prev_x=x, prev_y=y),
        edible=Edible(
            points=0,  # no points for poisoned apples
            growth=0,  # no growth - just death
            speed_modifier=1.0,  # no speed change
        ),
        renderable=Renderable(
            shape="circle",
            color=Color(color[0], color[1], color[2]),
            size=grid_size,
        ),
    )

    # add poisoned component to mark as deadly
    poisoned_apple.poisoned = Poisoned(deadly=True)

    # register entity with world and return ID
    entity_id = world.registry.add(poisoned_apple)
    return entity_id
