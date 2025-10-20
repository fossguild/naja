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

"""Fixed timestep implementation."""

import pygame
from typing import Optional


class GameClock:
    """Game clock with fixed timestep and frame limiting.

    This class provides consistent timing for the game loop, ensuring
    smooth gameplay regardless of frame rate variations.
    """

    def __init__(self, target_fps: int = 60):
        """Initialize the game clock.

        Args:
            target_fps: Target frames per second for frame limiting
        """
        self.target_fps = target_fps
        self.target_frame_time = 1000.0 / target_fps  # milliseconds per frame
        self.last_time: Optional[float] = None
        self.accumulator: float = 0.0
        self.delta_time: float = 0.0

    def tick(self, fps_limit: Optional[int] = None) -> float:
        """Tick the clock and return delta time in milliseconds.

        Args:
            fps_limit: Optional FPS limit override (uses target_fps if None)

        Returns:
            Delta time in milliseconds since last tick
        """
        current_time = pygame.time.get_ticks()

        if self.last_time is None:
            self.last_time = current_time
            self.delta_time = 0.0
            return self.delta_time

        # Calculate frame time
        frame_time = current_time - self.last_time
        self.last_time = current_time

        # Apply frame limiting if specified
        if fps_limit is not None:
            target_frame_time = 1000.0 / fps_limit
        else:
            target_frame_time = self.target_frame_time

        # Cap frame time to prevent spiral of death
        max_frame_time = target_frame_time * 2.0
        frame_time = min(frame_time, max_frame_time)

        # Store delta time
        self.delta_time = frame_time

        # Frame limiting
        if frame_time < target_frame_time:
            sleep_time = target_frame_time - frame_time
            pygame.time.wait(int(sleep_time))
            self.delta_time = target_frame_time

        return self.delta_time

    def get_delta_time(self) -> float:
        """Get the last calculated delta time in milliseconds.

        Returns:
            Delta time in milliseconds
        """
        return self.delta_time

    def get_fps(self) -> float:
        """Get current FPS based on delta time.

        Returns:
            Current FPS
        """
        if self.delta_time == 0:
            return 0.0
        return 1000.0 / self.delta_time

    def reset(self) -> None:
        """Reset the clock state."""
        self.last_time = None
        self.accumulator = 0.0
        self.delta_time = 0.0
