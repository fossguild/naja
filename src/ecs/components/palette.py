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

"""Palette component."""

from dataclasses import dataclass
from typing import Tuple


@dataclass
class Palette:
    """Color palette for rendering an entity.

    Stores RGB color tuples for different parts of an entity.
    Used by: Snake (head and tail colors), Apple, Obstacle
    """

    primary_color: Tuple[int, int, int] = (0, 255, 0)  # default green for snake head
    secondary_color: Tuple[int, int, int] = (
        0,
        170,
        0,
    )  # default dark green for snake tail
