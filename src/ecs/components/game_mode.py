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

"""Game mode component for tracking selected game mode."""

from dataclasses import dataclass
from enum import Enum, auto


class GameModeType(Enum):
    """Enum for different game modes."""

    CLASSIC = auto()  # default mode with only apples
    MORE_FRUITS = auto()  # mode with multiple fruit varieties
    POISONED_APPLE = auto()  # mode with deadly poisoned apples


@dataclass
class GameMode:
    """Component for tracking the selected game mode.

    This component is attached to the game singleton entity to track
    which game mode is currently selected.

    Used by: Game entity (singleton)
    Read by: Gameplay systems (spawn, collision, etc.)
    Written by: MenuScene, GameModesScene
    """

    mode: GameModeType = GameModeType.CLASSIC
    available: bool = True  # whether this mode is available to play
