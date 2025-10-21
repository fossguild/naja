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

"""Command converter for translating pygame events to typed commands."""

import pygame
from typing import Optional, Tuple, Callable
from src.ecs.components.commands import (
    Command,
    MoveCommand,
    PauseCommand,
    QuitCommand,
    OpenSettingsCommand,
    ToggleMusicCommand,
    RandomizePaletteCommand,
)


class CommandConverter:
    """Converts pygame events into typed commands.

    Responsibilities:
    - Event-to-command translation
    - Movement validation (180° turn prevention)
    - Command generation
    """

    def __init__(
        self, get_current_direction: Optional[Callable[[], Tuple[int, int]]] = None
    ):
        """Initialize the CommandConverter.

        Args:
            get_current_direction: Optional callback to get current snake direction (dx, dy)
        """
        self._get_current_direction = get_current_direction

    def handle_in_game_event(self, event: pygame.event.Event) -> list[Command]:
        """Convert raw pygame event into typed commands.

        This method processes a single pygame event and returns a list of commands
        that should be applied by the main loop. Commands are returned in the order
        they should be applied.

        Args:
            event: Pygame event to process

        Returns:
            list[Command]: List of commands to apply (may be empty)
        """
        commands = []

        # Handle quit event (window close button)
        if event.type == pygame.QUIT:
            commands.append(QuitCommand())
            return commands

        # Handle keyboard events
        if event.type == pygame.KEYDOWN:
            key = event.key

            # Movement keys - check for 180° turn prevention
            current_dx, current_dy = self._get_current_direction_safe()

            if key in (pygame.K_DOWN, pygame.K_s):
                if self._is_direction_valid(0, 1, current_dx, current_dy):
                    commands.append(MoveCommand(dx=0, dy=1))

            elif key in (pygame.K_UP, pygame.K_w):
                if self._is_direction_valid(0, -1, current_dx, current_dy):
                    commands.append(MoveCommand(dx=0, dy=-1))

            elif key in (pygame.K_RIGHT, pygame.K_d):
                if self._is_direction_valid(1, 0, current_dx, current_dy):
                    commands.append(MoveCommand(dx=1, dy=0))

            elif key in (pygame.K_LEFT, pygame.K_a):
                if self._is_direction_valid(-1, 0, current_dx, current_dy):
                    commands.append(MoveCommand(dx=-1, dy=0))

            # Control keys
            elif key == pygame.K_q:
                commands.append(QuitCommand())

            elif key == pygame.K_p:
                commands.append(PauseCommand())

            elif key in (pygame.K_m, pygame.K_ESCAPE):
                commands.append(OpenSettingsCommand())

            elif key == pygame.K_n:
                commands.append(ToggleMusicCommand())

            elif key == pygame.K_c:
                commands.append(RandomizePaletteCommand())

        return commands

    def _get_current_direction_safe(self) -> Tuple[int, int]:
        """Get current direction from callback or return (0, 0).

        Returns:
            Tuple[int, int]: Current (dx, dy) direction or (0, 0) if unavailable
        """
        if self._get_current_direction:
            try:
                return self._get_current_direction()
            except Exception:
                pass
        return (0, 0)

    def _is_direction_valid(
        self, dx: int, dy: int, current_dx: int, current_dy: int
    ) -> bool:
        """Check if direction change is valid (prevents 180° turns).

        Args:
            dx: New X direction (-1, 0, 1)
            dy: New Y direction (-1, 0, 1)
            current_dx: Current X direction
            current_dy: Current Y direction

        Returns:
            bool: True if direction change is valid
        """
        # Horizontal movement - allow if not opposite direction
        if dx != 0 and current_dx != -dx:
            return True
        # Vertical movement - allow if not opposite direction
        if dy != 0 and current_dy != -dy:
            return True
        return False
