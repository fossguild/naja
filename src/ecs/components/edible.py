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

"""Edible component (Ex: An apple, a pear)."""

from dataclasses import dataclass


@dataclass
class Edible:
    """Marks an entity as edible by the snake.

    Contains properties for scoring, growth, and speed effects when consumed.
    Used by: Apple, Grape, Orange
    """

    points: int = 10  # how many points earned by fruit
    growth: int = 1  # how many segments to add to snake by fruit
    speed_modifier: float = (
        1.1  # speed multiplier when eaten (e.g., 1.1 = +10%, 0.8 = -20%)
    )
