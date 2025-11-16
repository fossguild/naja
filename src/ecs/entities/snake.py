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

"""Snake entity."""

from dataclasses import dataclass

from ecs.entities.entity import Entity, EntityType
from ecs.components.position import Position
from ecs.components.velocity import Velocity
from ecs.components.snake_body import SnakeBody
from ecs.components.interpolation import Interpolation
from ecs.components.renderable import Renderable
from ecs.components.input_buffer import InputBuffer


@dataclass
class Snake(Entity):
    """Snake entity component composition.

    Defines the components that make up a snake entity:
    - position: head position in grid
    - velocity: movement direction and speed
    - body: tail segments as Position list
    - interpolation: smooth rendering data
    - renderable: visual appearance (contains head color)

    Note: Snake colors are now stored in renderable.color (head) and
    retrieved from ColorScheme or constants for tail color.
    """

    position: Position
    velocity: Velocity
    body: SnakeBody
    interpolation: Interpolation
    renderable: Renderable
    input_buffer: InputBuffer

    def get_type(self) -> EntityType:
        """Get the type of this entity.

        Returns:
            EntityType.SNAKE
        """
        return EntityType.SNAKE
