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

"""Box entity for Box Mode."""

from dataclasses import dataclass

from ecs.entities.entity import Entity, EntityType
from ecs.components.position import Position
from ecs.components.box import Box as BoxComponent
from ecs.components.renderable import Renderable


@dataclass
class Box(Entity):
    """Box entity component composition.

    Defines the components that make up a box entity:
    - position: location in grid
    - box: points and growth properties
    - renderable: visual appearance
    """

    position: Position
    box: BoxComponent
    renderable: Renderable

    def get_type(self) -> EntityType:
        """Get the type of this entity.

        Returns:
            EntityType.BOX
        """
        return EntityType.BOX
