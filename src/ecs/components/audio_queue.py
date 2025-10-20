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

"""Audio queue component."""

from dataclasses import dataclass
from typing import List


@dataclass
class AudioQueue:
    """Component for managing audio playback queue.

    Contains:
    - sfx_queue: List of sound effects to play
    - music_enabled: Whether background music is enabled

    Used by: AudioSystem
    """

    sfx_queue: List[str]
    music_enabled: bool
