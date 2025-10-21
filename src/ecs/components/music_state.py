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

"""Music state component."""

from dataclasses import dataclass


@dataclass
class MusicState:
    """Component for managing background music state.

    Contains:
    - enabled: Whether background music is enabled
    - current_track: Name of currently playing track
    - volume: Music volume (0.0 to 1.0)
    - is_playing: Whether music is currently playing
    - is_paused: Whether music is paused

    Used by: AudioSystem
    """

    enabled: bool = True
    current_track: str = "background"
    volume: float = 0.2
    is_playing: bool = False
    is_paused: bool = False
