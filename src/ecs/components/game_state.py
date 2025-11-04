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

"""Game state component for managing game flow state."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class GameState:
    """Global game state component.

    This component is attached to a singleton game entity to track
    overall game state like pause, game over, and scene transitions.

    Used by: Game entity (singleton)
    Read by: Most systems (to check paused state)
    Written by: InputSystem, CollisionSystem
    """

    paused: bool = False
    game_over: bool = False
    death_reason: str = ""
    next_scene: Optional[str] = None
    settings_menu_open: bool = False
    settings_selected_index: int = 0
    settings_menu_item_count: int = 0  # total items including "Return to Menu"
