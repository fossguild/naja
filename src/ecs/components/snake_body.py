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

"""Snake body component."""

from dataclasses import dataclass, field

from src.ecs.components.position import Position


@dataclass
class SnakeBody:
    """Snake body segments and growth state.
    
    Stores the history of segment positions and pending growth.
    Head position is stored in the entity's Position component.
    Used by: Snake
    """

    segments: list[Position] = field(default_factory=list)
    growth_queue: int = 0
    alive: bool = True
