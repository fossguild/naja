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

"""Interpolation component."""

from dataclasses import dataclass


@dataclass
class Interpolation:
    """Smooth rendering data between ticks.
    
    Stores previous and target positions for smooth animation.
    Alpha is the interpolation factor [0.0, 1.0].
    Used by: Snake (for smooth movement)
    """

    prev_x: int = 0
    prev_y: int = 0
    target_x: int = 0
    target_y: int = 0
    draw_x: float = 0.0
    draw_y: float = 0.0
    move_progress: float = 0.0
