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

"""Box component for Box Mode."""

from dataclasses import dataclass


@dataclass
class Box:
    """Component for box entities that can be pushed by the snake.

    Contains:
    - points: Points earned when box reaches hole
    - growth: Segments to add to snake when box reaches hole

    Used by: Box entities in Box Mode
    """

    points: int = 10  # points earned when box reaches hole
    growth: int = 1  # how many segments to add to snake

