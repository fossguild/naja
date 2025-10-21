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

"""Settings applicator for applying game configuration changes.

This module provides the SettingsApplicator class that handles applying
settings changes to the game, including window resizing, font reloading,
and entity recreation.
"""

import pygame
from typing import Any


class SettingsApplicator:
    """Handles application of settings changes to game state.

    Responsibilities:
    - Window resizing when grid size changes
    - Font reloading with new dimensions
    - Entity recreation (snake, apples, obstacles)
    - Music state management
    - Detecting which changes require game reset

    This is a transitional component during ECS migration that bridges
    the old code architecture with the new ECS systems.
    """

    # Critical settings that require game reset
    CRITICAL_SETTINGS = [
        "cells_per_side",
        "obstacle_difficulty",
        "initial_speed",
        "number_of_apples",
        "electric_walls",
    ]

    def __init__(
        self,
        pygame_adapter: Any,
        state: Any,
        assets: Any,
        config: Any,
    ):
        """Initialize the SettingsApplicator.

        Args:
            pygame_adapter: PygameIOAdapter instance for display operations
            state: GameState instance (old code)
            assets: GameAssets instance for font management
            config: GameConfig instance for dimension calculations
        """
        self._pygame_adapter = pygame_adapter
        self._state = state
        self._assets = assets
        self._config = config
        self._settings_snapshot: dict[str, Any] = {}

    def snapshot_critical_settings(self, settings: Any) -> None:
        """Take a snapshot of critical settings before changes.

        Args:
            settings: GameSettings instance
        """
        self._settings_snapshot = {
            key: settings.get(key) for key in self.CRITICAL_SETTINGS
        }

    def needs_reset(self, settings: Any) -> bool:
        """Check if current settings differ from snapshot in critical ways.

        Args:
            settings: GameSettings instance

        Returns:
            bool: True if game reset is needed due to critical setting changes
        """
        if not self._settings_snapshot:
            return False

        return any(
            settings.get(key) != self._settings_snapshot.get(key)
            for key in self.CRITICAL_SETTINGS
        )

    def apply_settings(self, settings: Any, reset_objects: bool = False) -> None:
        """Apply settings to game state, potentially resizing window and recreating objects.

        Args:
            settings: GameSettings instance
            reset_objects: Whether to recreate game objects (snake, apples, obstacles)
        """
        if not all([self._state, self._assets, self._config]):
            raise RuntimeError("SettingsApplicator not properly initialized")

        old_grid = self._state.grid_size

        # Calculate new grid size from desired cells per side
        desired_cells = max(10, int(settings.get("cells_per_side")))
        new_grid_size = self._config.get_optimal_grid_size(desired_cells)

        # Calculate obstacles from difficulty
        new_width, new_height = self._config.calculate_window_size(new_grid_size)

        # Import here to avoid circular dependencies during migration
        from old_code.entities import Obstacle, Snake, Apple

        num_obstacles = Obstacle.calculate_obstacles_from_difficulty(
            settings.get("obstacle_difficulty"),
            new_width,
            new_grid_size,
            new_height,
        )

        # Validate and get apples count
        num_apples = settings.validate_apples_count(
            new_width, new_grid_size, new_height
        )

        # Control background music playback based on setting
        if settings.get("background_music"):
            pygame.mixer.music.unpause()
        else:
            pygame.mixer.music.pause()

        # Recompute window and recreate surface/fonts if grid changed
        if new_grid_size != old_grid:
            new_width, new_height = self._config.calculate_window_size(new_grid_size)
            self._state.arena = self._pygame_adapter.set_mode((new_width, new_height))

            # Import here to avoid circular dependencies
            from old_code.constants import WINDOW_TITLE

            self._pygame_adapter.set_caption(WINDOW_TITLE)

            # Update state's dimensions to match new grid size
            self._state.update_dimensions(new_width, new_height, new_grid_size)

            # Reload fonts with new width
            self._assets.reload_fonts(new_width)

            # Force reset_objects when grid size changes to prevent misalignment
            reset_objects = True

        # Recreate moving objects to reflect new geometry/speed
        if reset_objects:
            # Get current dimensions from state
            width = self._state.width
            height = self._state.height
            grid_size = self._state.grid_size

            # Recreate snake with initial speed
            self._state.snake = Snake(width, height, grid_size)
            self._state.snake.speed = float(settings.get("initial_speed"))

            # Create obstacles
            self._state.create_obstacles_constructively(num_obstacles)

            # Create multiple apples
            self._state.apples = []
            for _ in range(num_apples):
                apple = Apple(width, height, grid_size)
                apple.ensure_valid_position(self._state.snake, self._state.obstacles)
                # Also ensure it doesn't overlap with existing apples
                while any(
                    apple.x == a.x and apple.y == a.y for a in self._state.apples
                ):
                    apple.ensure_valid_position(
                        self._state.snake, self._state.obstacles
                    )
                self._state.apples.append(apple)

    def get_critical_settings_list(self) -> list[str]:
        """Get list of critical settings that require reset.

        Returns:
            list[str]: List of critical setting keys
        """
        return self.CRITICAL_SETTINGS.copy()
