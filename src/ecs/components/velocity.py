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

"""Velocity component."""

from dataclasses import dataclass


@dataclass
class Velocity:
    """Movement direction and speed.

    Direction is represented as discrete grid movement:
    - dx: -1 (left), 0 (still), 1 (right)
    - dy: -1 (up), 0 (still), 1 (down)

    Speed is in ticks per cell movement.
    Used by: Snake
    """

    dx: int = 1  # initial direction is right
    dy: int = 0
    speed: float = 10.0  # cells per second
