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

"""Settings menu handler for game configuration."""

import pygame
from src.core.rendering.pygame_surface_renderer import RenderEnqueue
from src.ecs.systems.assets import AssetsSystem


class SettingsResult:
    """Result returned by settings menu."""

    def __init__(self, needs_reset: bool = False, canceled: bool = False):
        self.needs_reset = needs_reset
        self.canceled = canceled


class SettingsHandler:
    """Handles settings menu navigation and editing.

    Responsibilities:
    - Settings menu navigation
    - Value editing
    - Detecting critical setting changes
    - Delegating rendering to RenderSystem
    """

    # Critical settings that require game reset
    CRITICAL_SETTINGS = [
        "cells_per_side",
        "obstacle_difficulty",
        "initial_speed",
        "number_of_apples",
        "electric_walls",
    ]

    def __init__(self, renderer: RenderEnqueue, assets: AssetsSystem):
        """Initialize the SettingsHandler.

        Args:
            renderer: RenderEnqueue view to queue draw commands
            assets: AssetsSystem instance for accessing fonts and sprites
        """
        self._renderer = renderer
        self._assets = assets

    def run_settings_menu(self, io_adapter, settings) -> SettingsResult:
        """Run the settings menu loop until user confirms or cancels.

        Args:
            io_adapter: PygameIOAdapter instance for event handling and display updates
            settings: GameSettings instance to modify

        Returns:
            SettingsResult: Contains needs_reset and canceled flags
        """
        selected_index = 0

        # Snapshot original values of critical settings that need reset
        original_values = {key: settings.get(key) for key in self.CRITICAL_SETTINGS}

        # Event loop
        while True:
            # Get current settings values as dict for renderer
            settings_values = {
                field["key"]: settings.get(field["key"])
                for field in settings.MENU_FIELDS
            }

            # Render settings menu using renderer's built-in method
            self._renderer.draw_settings_menu(
                settings.MENU_FIELDS, selected_index, settings_values
            )
            io_adapter.update_display()

            # Process events
            for event in io_adapter.get_events():
                if event.type == pygame.QUIT:
                    # User closed window - revert changes
                    for key, value in original_values.items():
                        settings.set(key, value)
                    return SettingsResult(needs_reset=False, canceled=True)

                if event.type == pygame.KEYDOWN:
                    key = event.key

                    # Exit menu (save changes)
                    if key in (pygame.K_ESCAPE, pygame.K_RETURN):
                        # Check if critical settings changed
                        needs_reset = any(
                            settings.get(k) != original_values[k]
                            for k in self.CRITICAL_SETTINGS
                        )
                        return SettingsResult(needs_reset=needs_reset, canceled=False)

                    # Navigate down
                    elif key in (pygame.K_DOWN, pygame.K_s):
                        selected_index = (selected_index + 1) % len(
                            settings.MENU_FIELDS
                        )

                    # Navigate up
                    elif key in (pygame.K_UP, pygame.K_w):
                        selected_index = (selected_index - 1) % len(
                            settings.MENU_FIELDS
                        )

                    # Decrease value
                    elif key in (pygame.K_LEFT, pygame.K_a):
                        settings.step_setting(settings.MENU_FIELDS[selected_index], -1)

                    # Increase value
                    elif key in (pygame.K_RIGHT, pygame.K_d):
                        settings.step_setting(settings.MENU_FIELDS[selected_index], +1)

                    # Random colors (special key)
                    elif key == pygame.K_c:
                        settings.randomize_colors()
