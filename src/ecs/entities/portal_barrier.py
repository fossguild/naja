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

"""Portal Barrier entity for Portal Barrier Mode."""

from dataclasses import dataclass
from typing import Optional

from ecs.entities.entity import Entity, EntityType
from ecs.components.position import Position
from ecs.components.portal_barrier import PortalBarrier, PortalBarrierTag
from ecs.components.renderable import Renderable


@dataclass
class PortalBarrierEntity(Entity):
    """Portal Barrier entity component composition.

    Defines the components that make up a portal barrier entity:
    - position: location of entry block in grid
    - portal_barrier: the two-block barrier configuration (entry/exit blocks)
    - tag: marker component
    - renderable: visual representation for entry block
    """

    position: Position
    portal_barrier: PortalBarrier
    tag: PortalBarrierTag
    renderable: Optional[Renderable] = None

    def get_type(self) -> EntityType:
        """Get the type of this entity.

        Returns:
            EntityType.PORTAL_BARRIER
        """
        return EntityType.PORTAL_BARRIER
