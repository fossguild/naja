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

"""Hole entity for Box Mode."""

from dataclasses import dataclass

from ecs.entities.entity import Entity, EntityType
from ecs.components.position import Position
from ecs.components.hole import Hole as HoleComponent
from ecs.components.renderable import Renderable


@dataclass
class Hole(Entity):
    """Hole entity component composition.

    Defines the components that make up a hole entity:
    - position: location in grid
    - hole: marker component
    - renderable: visual appearance
    """

    position: Position
    hole: HoleComponent
    renderable: Renderable

    def get_type(self) -> EntityType:
        """Get the type of this entity.

        Returns:
            EntityType.HOLE
        """
        return EntityType.HOLE

