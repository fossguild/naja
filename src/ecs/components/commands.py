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

"""Command protocol for typed user actions.

Commands are immutable data structures that represent user intentions.
They are created by UISystem from pygame events and applied by the main loop
in deterministic order.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class MoveCommand:
    """Command to change snake direction.

    Attributes:
        dx: X direction (-1, 0, 1)
        dy: Y direction (-1, 0, 1)
    """

    dx: int
    dy: int

    def __post_init__(self):
        """Validate direction values."""
        if self.dx not in (-1, 0, 1) or self.dy not in (-1, 0, 1):
            raise ValueError(f"Invalid direction: ({self.dx}, {self.dy})")
        if self.dx == 0 and self.dy == 0:
            raise ValueError("Direction cannot be (0, 0)")
        if self.dx != 0 and self.dy != 0:
            raise ValueError("Direction must be horizontal or vertical")


@dataclass(frozen=True)
class PauseCommand:
    """Command to toggle pause state."""


@dataclass(frozen=True)
class QuitCommand:
    """Command to exit the game."""


@dataclass(frozen=True)
class OpenSettingsCommand:
    """Command to open settings menu."""


@dataclass(frozen=True)
class ToggleMusicCommand:
    """Command to toggle background music on/off."""


@dataclass(frozen=True)
class RandomizePaletteCommand:
    """Command to randomize color palette."""


@dataclass(frozen=True)
class ApplySettingsCommand:
    """Command to apply pending settings changes.

    Attributes:
        reset_objects: Whether to recreate game objects (snake, apples, obstacles)
    """

    reset_objects: bool = False


# Type alias for all command types
Command = (
    MoveCommand
    | PauseCommand
    | QuitCommand
    | OpenSettingsCommand
    | ToggleMusicCommand
    | RandomizePaletteCommand
    | ApplySettingsCommand
)
