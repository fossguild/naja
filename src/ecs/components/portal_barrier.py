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

"""Portal Barrier components for Portal Barrier Mode."""

from dataclasses import dataclass


@dataclass
class PortalBarrierTag:
    """Marker component for portal barrier entities.

    Tag-only component with no data fields.
    Used by: PortalBarrier entity
    """


@dataclass
class PortalBarrier:
    """Component representing a two-block portal barrier.

    A portal barrier consists of two adjacent blocks on the grid.
    When the snake's head enters either block, it teleports
    to the opposite block and continues movement in the same direction.

    Contains:
    - block1_x: X coordinate of first block
    - block1_y: Y coordinate of first block
    - block2_x: X coordinate of second block
    - block2_y: Y coordinate of second block

    The barrier works bidirectionally:
    - If snake enters block1, it exits at block2
    - If snake enters block2, it exits at block1

    Used by: CollisionSystem
    """

    block1_x: int
    block1_y: int
    block2_x: int
    block2_y: int
