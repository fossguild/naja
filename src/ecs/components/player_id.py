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

"""Player ID component for distinguishing players in PvP mode."""

from dataclasses import dataclass


@dataclass
class PlayerID:
    """Identifies which player controls this snake.

    Used by: Snake (in Player vs Player mode)
    """

    player_number: int  # 1 for Player 1 (WASD), 2 for Player 2 (Arrows)
    score: int = 0  # individual player score
