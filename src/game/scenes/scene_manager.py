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

"""Scene manager for handling scene transitions."""

from __future__ import annotations

from typing import Dict, Optional

from game.scenes.base_scene import BaseScene


class SceneManager:
    """Manages scene transitions and lifecycle."""

    def __init__(self):
        """Initialize the scene manager."""
        self._scenes: Dict[str, BaseScene] = {}
        self._current_scene: Optional[BaseScene] = None
        self._next_scene_name: Optional[str] = None

    def register_scene(self, name: str, scene: BaseScene) -> None:
        """Register a scene with the manager.

        Args:
            name: Scene name/identifier
            scene: Scene instance
        """
        self._scenes[name] = scene

    def set_scene(self, name: str) -> None:
        """Set the current scene.

        Args:
            name: Name of scene to switch to
        """
        if name not in self._scenes:
            raise ValueError(f"Scene '{name}' not registered")

        self._next_scene_name = name

    def update(self, dt_ms: float) -> None:
        """Update the current scene and handle transitions.

        Args:
            dt_ms: Delta time in milliseconds
        """
        # Handle scene transition
        if self._next_scene_name:
            self._transition_to_scene(self._next_scene_name)
            self._next_scene_name = None

        # Update current scene
        if self._current_scene:
            next_scene = self._current_scene.update(dt_ms)
            if next_scene:
                self.set_scene(next_scene)

    def render(self) -> None:
        """Render the current scene."""
        if self._current_scene:
            self._current_scene.render()

    def _transition_to_scene(self, name: str) -> None:
        """Transition to a new scene.

        Args:
            name: Name of scene to transition to
        """
        print(f"Transitioning to scene: {name}")

        # Exit current scene
        if self._current_scene:
            self._current_scene.on_exit()

        # Enter new scene
        self._current_scene = self._scenes[name]
        self._current_scene.on_enter()

        print(f"Now in scene: {name}")

    @property
    def current_scene(self) -> Optional[BaseScene]:
        """Get the current scene.

        Returns:
            Current scene instance or None
        """
        return self._current_scene

    @property
    def current_scene_name(self) -> Optional[str]:
        """Get the current scene name.

        Returns:
            Current scene name or None
        """
        for name, scene in self._scenes.items():
            if scene is self._current_scene:
                return name
        return None
