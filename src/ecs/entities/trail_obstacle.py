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

"""Trail obstacle entity for Trail Mode."""

from dataclasses import dataclass
from typing import Optional

from ecs.entities.entity import Entity, EntityType
from ecs.components.position import Position
from ecs.components.trail_obstacle import TrailObstacleTag
from ecs.components.renderable import Renderable


@dataclass
class TrailObstacle(Entity):
    """Trail obstacle entity created during Trail Mode gameplay.

    Trail obstacles are dynamically created as the snake moves,
    marking every position the snake's head passes through.

    Components:
    - position: location in grid where trail was left
    - tag: marker to identify as trail obstacle
    - renderable: visual representation (optional, for ECS rendering)
    """

    position: Position
    tag: TrailObstacleTag
    renderable: Optional[Renderable] = None

    def get_type(self) -> EntityType:
        """Get the type of this entity.

        Returns:
            EntityType.OBSTACLE (trail obstacles are treated as obstacles)
        """
        return EntityType.OBSTACLE
