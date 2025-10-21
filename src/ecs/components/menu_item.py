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

"""Menu item component."""

from dataclasses import dataclass


@dataclass
class MenuItem:
    """Component for menu item entities.

    Contains:
    - text: Display text for the menu item
    - action: Action identifier to execute when selected
    - selected: Whether this item is currently selected

    Used by: UISystem for menu rendering and interaction
    """

    text: str
    action: str
    selected: bool
