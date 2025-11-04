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

This module provides a thin abstraction layer over pygame operations for
better testability and separation of concerns. It wraps:
- Event polling
- Screen initialization and updates
- Basic drawing primitives (rect, circle, line)
- Surface creation

The adapter provides no game logic - it's purely an IO interface.
"""

import pygame
from typing import List, Tuple
from pygame import Surface, Rect


class PygameIOAdapter:
    """Adapter for pygame IO operations.

    This class wraps pygame operations to provide a clean interface
    for event handling, screen management, and basic drawing operations.
    All methods are pure IO operations with no game logic.
    """

    def __init__(self):
        """Initialize the pygame IO adapter."""

    def get_events(self) -> List[pygame.event.Event]:
        """Get all pending pygame events.

        Returns:
            List of pygame events that occurred since last call.
        """
        return pygame.event.get()

    def get_resize_event(self) -> Tuple[int, int] | None:
        """Check for VIDEORESIZE event and return new window size.

        Only checks for resize events without consuming other events.
        Uses pygame.event.get(pygame.VIDEORESIZE) to isolate resize events.

        Returns:
            Tuple of (width, height) if window was resized, None otherwise
        """
        # Get only VIDEORESIZE events, leaving other events in queue
        resize_events = pygame.event.get(pygame.VIDEORESIZE)
        if resize_events:
            # Return size from first resize event, put others back
            size = resize_events[0].size
            for event in resize_events[1:]:
                pygame.event.post(event)
            return size
        return None

    def wait_for_event(self) -> pygame.event.Event:
        """Wait for a single pygame event.

        Returns:
            The next pygame event
        """
        return pygame.event.wait()

    def set_mode(self, size: Tuple[int, int], flags: int = 0) -> Surface:
        """Create a new display surface.

        Args:
            size: Width and height of the display surface
            flags: Optional display flags

        Returns:
            New display surface
        """
        return pygame.display.set_mode(size, flags)

    def set_caption(self, title: str) -> None:
        """Set the window caption/title.

        Args:
            title: Window title text
        """
        pygame.display.set_caption(title)

    def update_display(self) -> None:
        """Update the display surface to screen."""
        pygame.display.update()

    def quit(self) -> None:
        """Quit pygame and clean up resources."""
        pygame.quit()

    def init(self) -> None:
        """Initialize pygame subsystems."""
        pygame.init()

    def init_mixer(self) -> None:
        """Initialize pygame mixer for audio."""
        pygame.mixer.init()

    def create_surface(self, size: Tuple[int, int], flags: int = 0) -> Surface:
        """Create a new surface.

        Args:
            size: Width and height of the surface
            flags: Optional surface flags (e.g., pygame.SRCALPHA)

        Returns:
            New surface
        """
        return pygame.Surface(size, flags)

    def draw_rect(
        self, surface: Surface, color: Tuple[int, int, int], rect: Rect, width: int = 0
    ) -> Rect:
        """Draw a rectangle.

        Args:
            surface: Surface to draw on
            color: RGB color tuple
            rect: Rectangle to draw
            width: Line width (0 for filled rectangle)

        Returns:
            Rectangle that was drawn
        """
        return pygame.draw.rect(surface, color, rect, width)

    def draw_circle(
        self,
        surface: Surface,
        color: Tuple[int, int, int],
        center: Tuple[int, int],
        radius: int,
        width: int = 0,
    ) -> Rect:
        """Draw a circle.

        Args:
            surface: Surface to draw on
            color: RGB color tuple
            center: Center coordinates (x, y)
            radius: Circle radius
            width: Line width (0 for filled circle)

        Returns:
            Bounding rectangle of the circle
        """
        return pygame.draw.circle(surface, color, center, radius, width)

    def draw_line(
        self,
        surface: Surface,
        color: Tuple[int, int, int],
        start_pos: Tuple[int, int],
        end_pos: Tuple[int, int],
        width: int = 1,
    ) -> Rect:
        """Draw a line.

        Args:
            surface: Surface to draw on
            color: RGB color tuple
            start_pos: Start coordinates (x, y)
            end_pos: End coordinates (x, y)
            width: Line width

        Returns:
            Bounding rectangle of the line
        """
        return pygame.draw.line(surface, color, start_pos, end_pos, width)

    def create_rect(self, x: int, y: int, width: int, height: int) -> Rect:
        """Create a rectangle.

        Args:
            x: Left coordinate
            y: Top coordinate
            width: Rectangle width
            height: Rectangle height

        Returns:
            New rectangle
        """
        return pygame.Rect(x, y, width, height)
