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

"""Hunger component."""

from dataclasses import dataclass, field


@dataclass
class Hunger:
    """Hunger/starvation timer for the snake.

    The snake must eat apples before hunger reaches 0 or it dies.
    Eating an apple resets the hunger timer to max_time.

    Attributes:
        current_time: Current hunger timer value in seconds (counts down)
        max_time: Maximum hunger time before starvation death (default: 10.0 seconds)

    Used by: Snake entity (singleton pattern for now)
    """

    current_time: float = field(default=10.0)
    max_time: float = field(default=10.0)
