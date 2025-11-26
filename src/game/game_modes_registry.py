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

"""Central definition of the available game modes."""

GameModeType = str

CLASSIC_MODE_NAME = "Classic Snake Game"
MOVING_APPLE_MODE_NAME = "Moving Apple"
HEAD_TAIL_SWITCH_NAME = "Head-Tail Swap"
CHEESE_MODE_NAME = "Cheese Mode"
AUTOPLAY_MODE_NAME = "AutoPlay"
GAME_MODE_TELEPORT = "Teleport"

ACTUAL_GAME_MODES = [
    {
        "name": CLASSIC_MODE_NAME,
        "description": "Classic snake gameplay with stationary apples and default settings.",
    },
    {
        "name": MOVING_APPLE_MODE_NAME,
        "description": "Apples drift slowly around the board, forcing constant pursuit.",
    },
    {
        "name": HEAD_TAIL_SWITCH_NAME,
        "description": "State toggle when the snake consumes an apple.",
    },
    {
        "name": CHEESE_MODE_NAME,
        "description": "Snake body has holes - pass through them safely, but avoid solid segments!",
    },
    {
        "name": AUTOPLAY_MODE_NAME,
        "description": "The snake plays itself, the player just watches.",
    },
    {
        "name": GAME_MODE_TELEPORT,
        "description": "Collect an apple to warp to the other one, maintaining your direction.",
    },
]

RANDOM_MODE_LABEL = "Random"
RANDOM_MODE_INDEX = len(ACTUAL_GAME_MODES)

__all__ = [
    "CLASSIC_MODE_NAME",
    "MOVING_APPLE_MODE_NAME",
    "CHEESE_MODE_NAME",
    "AUTOPLAY_MODE_NAME",
    "GAME_MODE_TELEPORT",
    "ACTUAL_GAME_MODES",
    "RANDOM_MODE_LABEL",
    "RANDOM_MODE_INDEX",
]
