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

"""Input state component."""

from dataclasses import dataclass
from typing import Set


@dataclass
class InputState:
    """Component for tracking input state.
    
    Contains:
    - keys_pressed: Set of currently pressed key names
    - mouse_pos: Current mouse position as (x, y) tuple
    
    Used by: InputSystem for capturing user input
    """
    keys_pressed: Set[str]
    mouse_pos: tuple[int, int]
