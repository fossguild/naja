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

"""Speed boost component for Speed Boost Mode.

Tracks the state of temporary speed boosts granted when eating apples.
"""

from dataclasses import dataclass


@dataclass
class SpeedBoost:
    """Component tracking speed boost state.

    Used by: Snake entity (when Speed Boost Mode is enabled)
    Read by: MovementSystem (to apply speed multiplier)
    Written by: SpeedBoostSystem (to manage boost timing)

    Attributes:
        active: Whether the speed boost is currently active
        remaining_time: Time left in seconds before boost expires
        multiplier: Speed multiplier applied when boost is active
        duration: Total duration of boost in seconds
    """

    active: bool = False
    remaining_time: float = 0.0
    multiplier: float = 2.0  # 2x speed when boosted
    duration: float = 3.0  # boost lasts 3 seconds

    def activate(self) -> None:
        """Activate the speed boost and reset the timer."""
        self.active = True
        self.remaining_time = self.duration

    def deactivate(self) -> None:
        """Deactivate the speed boost."""
        self.active = False
        self.remaining_time = 0.0
