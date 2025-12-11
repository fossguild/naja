
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

"""Lights Out mode state component.

Minimal state used by renderer and systems. Lights Out is an always-on
mode, only `radius` is required by runtime logic.
"""

from dataclasses import dataclass


@dataclass
class LightsOutState:
    """State for Lights Out game mode.

    Only `radius` is kept because timing and duration-based fields are
    removed in favor of an always-on implementation driven by systems
    and rendering logic.
    """

    radius: int = 4  # grid cells of visible radius around snake head
