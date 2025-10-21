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

from src.ecs.components.position import Position
from src.ecs.components.velocity import Velocity
from src.ecs.components.snake_body import SnakeBody
from src.ecs.components.edible import Edible
from src.ecs.components.obstacle import ObstacleTag, Obstacle
from src.ecs.components.interpolation import Interpolation
from src.ecs.components.renderable import Renderable
from src.ecs.components.grid import Grid
from src.ecs.components.audio_queue import AudioQueue
from src.ecs.components.validated import Validated
from src.ecs.components.ui_state import UIState
from src.ecs.components.menu_item import MenuItem
from src.ecs.components.dialog import Dialog
from src.ecs.components.input_state import InputState

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
    "AudioQueue",
    "Validated",
    "UIState",
    "MenuItem",
    "Dialog",
    "InputState",
]
