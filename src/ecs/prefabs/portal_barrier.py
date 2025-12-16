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

"""Portal Barrier entity prefab factory."""

from typing import Optional

from ecs.world import World
from ecs.entities.portal_barrier import PortalBarrierEntity
from ecs.components.position import Position
from ecs.components.portal_barrier import PortalBarrier, PortalBarrierTag
from ecs.components.renderable import Renderable
from core.types.color import Color


def create_portal_barrier(
    world: World,
    block1_x: int,
    block1_y: int,
    block2_x: int,
    block2_y: int,
    grid_size: int,
    color: Optional[tuple[int, int, int]] = None,
) -> int:
    """Create a portal barrier entity with two interconnected blocks.

    Args:
        world: ECS world to create entity in
        block1_x: X position of first block in pixels (grid-aligned)
        block1_y: Y position of first block in pixels (grid-aligned)
        block2_x: X position of second block in pixels (grid-aligned)
        block2_y: Y position of second block in pixels (grid-aligned)
        grid_size: Size of each grid cell in pixels
        color: RGB color for portal barrier (default: cyan)

    Returns:
        Entity ID of the created portal barrier
    """
    if color is None:
        color = (0, 255, 255)  # cyan

    # Create portal barrier component with both blocks
    portal_barrier_component = PortalBarrier(
        block1_x=block1_x,
        block1_y=block1_y,
        block2_x=block2_x,
        block2_y=block2_y,
    )

    # Create renderable for the first block
    block1_renderable = Renderable(
        shape="square",
        color=Color(color[0], color[1], color[2]),
        size=grid_size,
    )

    tag = PortalBarrierTag()

    # Create the entity with Position set to first block
    entity = PortalBarrierEntity(
        position=Position(x=block1_x, y=block1_y, prev_x=block1_x, prev_y=block1_y),
        portal_barrier=portal_barrier_component,
        tag=tag,
        renderable=block1_renderable,
    )

    # Add to world registry and return entity ID
    entity_id = world.registry.add(entity)
    return entity_id
