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

"""Base scene class for the game."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from src.core.io.pygame_adapter import PygameIOAdapter
from src.core.rendering.pygame_surface_renderer import RenderEnqueue


class BaseScene(ABC):
    """Base class for all game scenes.

    Each scene represents a different state of the game (menu, gameplay, game over, etc.)
    and handles its own input, update, and rendering logic.
    """

    def __init__(
        self,
        pygame_adapter: PygameIOAdapter,
        renderer: RenderEnqueue,
        width: int,
        height: int,
    ):
        """Initialize the base scene.

        Args:
            pygame_adapter: Pygame IO adapter for input handling
            renderer: Renderer for drawing operations
            width: Scene width in pixels
            height: Scene height in pixels
        """
        self._pygame_adapter = pygame_adapter
        self._renderer = renderer
        self._width = width
        self._height = height
        self._next_scene: Optional[str] = None

    @abstractmethod
    def update(self, dt_ms: float) -> Optional[str]:
        """Update the scene logic.

        Args:
            dt_ms: Delta time in milliseconds since last update

        Returns:
            Name of next scene to transition to, or None to stay in current scene
        """
        pass

    @abstractmethod
    def render(self) -> None:
        """Render the scene."""
        pass

    def on_enter(self) -> None:
        """Called when entering this scene."""
        pass

    def on_exit(self) -> None:
        """Called when exiting this scene."""
        pass

    def get_next_scene(self) -> Optional[str]:
        """Get the next scene to transition to.

        Returns:
            Name of next scene, or None if no transition
        """
        return self._next_scene

    def set_next_scene(self, scene_name: Optional[str]) -> None:
        """Set the next scene to transition to.

        Args:
            scene_name: Name of next scene, or None for no transition
        """
        self._next_scene = scene_name

    def update_dimensions(self, width: int, height: int) -> None:
        """Update scene dimensions when window is resized.

        Args:
            width: New width in pixels
            height: New height in pixels
        """
        self._width = width
        self._height = height
