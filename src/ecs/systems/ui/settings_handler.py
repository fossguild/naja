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
        # track which sections are collapsed
        self._collapsed_sections = set()
        # note: initialization will happen in run_settings_menu when we have access to settings

    def _initialize_collapsed_sections(self, all_fields: list[dict]) -> None:
        """Initialize collapsed sections from field definitions (only once).

        Args:
            all_fields: All menu fields
        """
        if not self._collapsed_sections:  # only initialize if empty
            for field in all_fields:
                if field["type"] == "section" and field.get("collapsed", False):
                    self._collapsed_sections.add(field["key"])

    def _get_visible_fields(self, all_fields: list[dict]) -> list[dict]:
        """Get only the fields that should be visible based on section collapse state.

        Args:
            all_fields: All menu fields

        Returns:
            List of visible fields
        """
        visible = []
        for field in all_fields:
            # section headers are always visible
            if field["type"] == "section":
                visible.append(field)
            # regular fields are visible if they don't have a parent section,
            # or if their parent section is not collapsed
            else:
                parent = field.get("parent_section")
                if not parent or parent not in self._collapsed_sections:
                    visible.append(field)
        return visible

    def _toggle_section(self, section_key: str) -> None:
        """Toggle a section's collapsed state.

        Args:
            section_key: Key of the section to toggle
        """
        if section_key in self._collapsed_sections:
            self._collapsed_sections.remove(section_key)
        else:
            self._collapsed_sections.add(section_key)

    def run_settings_menu(self, io_adapter, settings) -> SettingsResult:
        """Run the settings menu loop until user confirms or cancels.

        Args:
            io_adapter: PygameIOAdapter instance for event handling and display updates
            settings: GameSettings instance to modify

        Returns:
            SettingsResult: Contains needs_reset and canceled flags
        """
        selected_index = 0

        # Initialize collapsed sections from field definitions (only once)
        self._initialize_collapsed_sections(settings.MENU_FIELDS)

        # Snapshot original values of critical settings that need reset
        original_values = {key: settings.get(key) for key in self.CRITICAL_SETTINGS}

        # Event loop
        while True:
            # Get visible fields (filtered by collapsed sections)
            visible_fields = self._get_visible_fields(settings.MENU_FIELDS)

            # Clamp selected index to visible range
            if selected_index >= len(visible_fields):
                selected_index = len(visible_fields) - 1
            if selected_index < 0:
                selected_index = 0

            # Get current settings values as dict for renderer
            # include section collapse state
            settings_values = {
                field["key"]: settings.get(field["key"])
                for field in settings.MENU_FIELDS
                if field["type"] != "section"
            }
            # add collapse state for sections
            for field in settings.MENU_FIELDS:
                if field["type"] == "section":
                    settings_values[field["key"]] = (
                        field["key"] not in self._collapsed_sections
                    )

            # Render settings menu using renderer's built-in method
            self._renderer.draw_settings_menu(
                visible_fields, selected_index, settings_values
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

                    # Exit menu (save changes) - only on ESC
                    if key == pygame.K_ESCAPE:
                        # Check if critical settings changed
                        needs_reset = any(
                            settings.get(k) != original_values[k]
                            for k in self.CRITICAL_SETTINGS
                        )
                        return SettingsResult(needs_reset=needs_reset, canceled=False)

                    # Enter key toggles section expand/collapse
                    elif key == pygame.K_RETURN:
                        current_field = visible_fields[selected_index]
                        if current_field["type"] == "section":
                            self._toggle_section(current_field["key"])

                    # Navigate down
                    elif key in (pygame.K_DOWN, pygame.K_s):
                        selected_index = (selected_index + 1) % len(visible_fields)

                    # Navigate up
                    elif key in (pygame.K_UP, pygame.K_w):
                        selected_index = (selected_index - 1) % len(visible_fields)

                    # Decrease value
                    elif key in (pygame.K_LEFT, pygame.K_a):
                        current_field = visible_fields[selected_index]
                        settings.step_setting(current_field, -1)

                    # Increase value
                    elif key in (pygame.K_RIGHT, pygame.K_d):
                        current_field = visible_fields[selected_index]
                        settings.step_setting(current_field, +1)

                    # Random colors (special key)
                    elif key == pygame.K_c:
                        settings.randomize_snake_colors()
