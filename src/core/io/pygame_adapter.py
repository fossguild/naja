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

"""Pygame event, screen, and draw wrappers.

This module provides a testable interface for pygame functionality,
separating game logic from I/O concerns. No game logic should be
implemented here - only pure I/O wrappers.
"""

from typing import Tuple
import pygame


class PygameAdapter:
    """Wrapper for pygame-specific I/O operations.

    This adapter provides a testable interface for pygame functionality,
    separating game logic from I/O concerns. No game logic should be
    implemented here - only pure I/O wrappers.
    """

    # ============================================
    # 1. INITIALIZATION
    # ============================================

    @staticmethod
    def init() -> None:
        """Initialize pygame."""
        pygame.init()

    @staticmethod
    def init_mixer() -> None:
        """Initialize pygame mixer for audio."""
        pygame.mixer.init()

    # ============================================
    # 2. SCREEN/DISPLAY
    # ============================================

    @staticmethod
    def create_display(
        width: int, height: int, flags: int = pygame.SCALED, vsync: int = 1
    ) -> pygame.Surface:
        """Create and return a display surface.

        Args:
            width: Display width in pixels
            height: Display height in pixels
            flags: Pygame display flags (default: SCALED)
            vsync: Enable vertical sync (default: 1)

        Returns:
            The created display surface
        """
        return pygame.display.set_mode((width, height), flags, vsync=vsync)

    @staticmethod
    def set_caption(title: str) -> None:
        """Set the window title.

        Args:
            title: Window title text
        """
        pygame.display.set_caption(title)

    @staticmethod
    def update_display() -> None:
        """Update the full display to the screen."""
        pygame.display.update()

    # ============================================
    # 3. EVENT HANDLING
    # ============================================

    @staticmethod
    def poll_events() -> list[pygame.event.Event]:
        """Get all events from the event queue.

        Returns:
            List of pygame events
        """
        return pygame.event.get()

    @staticmethod
    def wait_for_event() -> pygame.event.Event:
        """Wait for a single event (blocking).

        Returns:
            The next event from the queue
        """
        return pygame.event.wait()

    # ============================================
    # 4. DRAWING PRIMITIVES
    # ============================================

    @staticmethod
    def draw_rect(
        surface: pygame.Surface,
        color: Tuple[int, int, int] | Tuple[int, int, int, int],
        rect: pygame.Rect | Tuple[int, int, int, int],
        width: int = 0,
    ) -> pygame.Rect:
        """Draw a rectangle on a surface.

        Args:
            surface: Target surface to draw on
            color: RGB or RGBA color tuple
            rect: Rectangle as pygame.Rect or (x, y, width, height) tuple
            width: Line width (0 = filled rectangle)

        Returns:
            The drawn rectangle area
        """
        return pygame.draw.rect(surface, color, rect, width)

    @staticmethod
    def create_surface(width: int, height: int, flags: int = 0) -> pygame.Surface:
        """Create a new surface.

        Args:
            width: Surface width in pixels
            height: Surface height in pixels
            flags: Surface flags (e.g., pygame.SRCALPHA for alpha)

        Returns:
            The created surface
        """
        return pygame.Surface((width, height), flags)

    @staticmethod
    def create_rect(
        x: int | float, y: int | float, width: int | float, height: int | float
    ) -> pygame.Rect:
        """Create a pygame Rect object.

        Args:
            x: Left coordinate
            y: Top coordinate
            width: Rectangle width
            height: Rectangle height

        Returns:
            The created rectangle
        """
        return pygame.Rect(round(x), round(y), round(width), round(height))

    # ============================================
    # 5. TIME/CLOCK
    # ============================================

    @staticmethod
    def get_ticks() -> int:
        """Get the number of milliseconds since pygame.init() was called.

        Returns:
            Milliseconds as integer
        """
        return pygame.time.get_ticks()

    @staticmethod
    def create_clock() -> pygame.time.Clock:
        """Create a pygame Clock object for frame timing.

        Returns:
            A new Clock instance
        """
        return pygame.time.Clock()


# ============================================
# RE-EXPORT PYGAME CONSTANTS
# ============================================
# These constants are re-exported to make it easier to migrate code
# without having to import pygame directly everywhere

# Event types
QUIT = pygame.QUIT
KEYDOWN = pygame.KEYDOWN

# Display flags
SCALED = pygame.SCALED
SRCALPHA = pygame.SRCALPHA

# Key constants
K_DOWN = pygame.K_DOWN
K_UP = pygame.K_UP
K_LEFT = pygame.K_LEFT
K_RIGHT = pygame.K_RIGHT
K_s = pygame.K_s
K_w = pygame.K_w
K_a = pygame.K_a
K_d = pygame.K_d
K_p = pygame.K_p
K_q = pygame.K_q
K_m = pygame.K_m
K_n = pygame.K_n
K_c = pygame.K_c
K_ESCAPE = pygame.K_ESCAPE
K_SPACE = pygame.K_SPACE
K_RETURN = pygame.K_RETURN
