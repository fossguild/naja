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

"""Dialog component."""

from dataclasses import dataclass
from typing import List


@dataclass
class Dialog:
    """Component for dialog entities.
    
    Contains:
    - title: Title text displayed in dialog header
    - message: Main message text of the dialog
    - options: List of available options/buttons
    
    Used by: UISystem for dialog rendering and interaction
    """
    title: str
    message: str
    options: List[str]
