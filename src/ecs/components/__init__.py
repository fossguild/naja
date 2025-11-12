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

"""Components module."""

from ecs.components.position import Position
from ecs.components.velocity import Velocity
from ecs.components.snake_body import SnakeBody
from ecs.components.edible import Edible
from ecs.components.obstacle import ObstacleTag, Obstacle
from ecs.components.interpolation import Interpolation
from ecs.components.renderable import Renderable
from ecs.components.grid import Grid
from ecs.components.apple_config import AppleConfig
from ecs.components.color_scheme import ColorScheme
from ecs.components.game_state import GameState
from ecs.components.score import Score

__all__ = [
    "Position",
    "Velocity",
    "SnakeBody",
    "Edible",
    "ObstacleTag",
    "Obstacle",
    "Interpolation",
    "Renderable",
    "Grid",
    "AppleConfig",
    "ColorScheme",
    "GameState",
    "Score",
]
