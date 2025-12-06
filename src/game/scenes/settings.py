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

"""Settings scene."""

from __future__ import annotations

import pygame
from typing import Optional

from src.game.scenes.base_scene import BaseScene
from src.game.services.assets import GameAssets
from src.game.settings import GameSettings
from src.game.constants import ARENA_COLOR, MESSAGE_COLOR, SCORE_COLOR, GRID_COLOR


class SettingsScene(BaseScene):
    """Settings scene."""

    def __init__(
        self,
        pygame_adapter,
        renderer,
        width: int,
        height: int,
        assets: GameAssets,
        settings: GameSettings,
    ):
        """Initialize the settings scene.

        Args:
            pygame_adapter: Pygame IO adapter
            renderer: Renderer for drawing
            width: Scene width
            height: Scene height
            assets: Game assets
            settings: Game settings
        """
        super().__init__(pygame_adapter, renderer, width, height)
        self._assets = assets
        self._settings = settings
        self._selected_index = 0
        # track which sections are collapsed
        self._collapsed_sections = set()
        # initialize collapsed sections from field definitions (only once)
        for field in self._settings.MENU_FIELDS:
            if field["type"] == "section" and field.get("collapsed", False):
                self._collapsed_sections.add(field["key"])

    def _get_visible_fields(self) -> list[dict]:
        """Get only the fields that should be visible based on section collapse state.

        Returns:
            List of visible fields
        """
        visible = []
        for field in self._settings.MENU_FIELDS:
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

    def update(self, dt_ms: float) -> Optional[str]:
        """Update settings logic.

        Args:
            dt_ms: Delta time in milliseconds

        Returns:
            Next scene name or None
        """
        # Get visible fields
        visible_fields = self._get_visible_fields()

        # Clamp selected index to visible range
        if self._selected_index >= len(visible_fields):
            self._selected_index = len(visible_fields) - 1
        if self._selected_index < 0:
            self._selected_index = 0

        # Handle input
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return "menu"  # back to menu
                elif event.key == pygame.K_RETURN:
                    # toggle section if selected field is a section
                    current_field = visible_fields[self._selected_index]
                    print(
                        f"[DEBUG] Enter pressed on field: {current_field.get('label')} (type: {current_field.get('type')})"
                    )
                    if current_field["type"] == "section":
                        print(f"[DEBUG] Toggling section: {current_field['key']}")
                        self._toggle_section(current_field["key"])
                        print(f"[DEBUG] Collapsed sections: {self._collapsed_sections}")
                    else:
                        return "menu"  # back to menu
                elif event.key in (pygame.K_DOWN, pygame.K_s):
                    self._selected_index = (self._selected_index + 1) % len(
                        visible_fields
                    )
                elif event.key in (pygame.K_UP, pygame.K_w):
                    self._selected_index = (self._selected_index - 1) % len(
                        visible_fields
                    )
                elif event.key in (pygame.K_LEFT, pygame.K_a):
                    current_field = visible_fields[self._selected_index]
                    self._settings.step_setting(current_field, -1)
                    # apply music setting immediately if changed
                    if current_field["key"] == "background_music":
                        if self._settings.get("background_music"):
                            pygame.mixer.music.unpause()
                        else:
                            pygame.mixer.music.pause()
                elif event.key in (pygame.K_RIGHT, pygame.K_d):
                    current_field = visible_fields[self._selected_index]
                    self._settings.step_setting(current_field, +1)
                    # apply music setting immediately if changed
                    if current_field["key"] == "background_music":
                        if self._settings.get("background_music"):
                            pygame.mixer.music.unpause()
                        else:
                            pygame.mixer.music.pause()

        return None

    def render(self) -> None:
        """Render the settings screen."""
        # Clear screen
        self._renderer.fill(ARENA_COLOR)

        # Draw title
        title = self._assets.render_custom(
            "Settings", MESSAGE_COLOR, int(self._width / 12)
        )
        title_rect = title.get_rect(center=(self._width / 2, self._height / 10))
        self._renderer.blit(title, title_rect)

        # Get visible fields
        visible_fields = self._get_visible_fields()

        # Spacing and scroll parameters
        row_h = int(self._height * 0.06)
        visible_rows = int(self._height * 0.70 // row_h)
        top_index = max(0, self._selected_index - visible_rows + 3)
        padding_y = int(self._height * 0.22)

        # Draw visible rows
        for draw_i, field_i in enumerate(range(top_index, len(visible_fields))):
            if draw_i >= visible_rows:
                break
            f = visible_fields[field_i]

            # Handle section headers differently
            if f["type"] == "section":
                # section headers get a collapse indicator
                is_expanded = f["key"] not in self._collapsed_sections
                indicator = "v" if is_expanded else ">"
                label_text = f"{indicator} {f['label']}"
                if draw_i == 0:  # only print once per frame to avoid spam
                    print(
                        f"[DEBUG] Rendering section '{f['key']}': expanded={is_expanded}, collapsed_set={self._collapsed_sections}"
                    )

                # make section headers slightly larger
                text = self._assets.render_custom(
                    label_text,
                    SCORE_COLOR if field_i == self._selected_index else MESSAGE_COLOR,
                    int(self._width / 28),
                )
            else:
                # regular fields
                val = self._settings.get(f["key"])
                formatted_val = self._settings.format_setting_value(
                    f,
                    val,
                    self._width,
                    20,  # grid_size placeholder
                )
                text = self._assets.render_custom(
                    f"{f['label']}: {formatted_val}",
                    SCORE_COLOR if field_i == self._selected_index else MESSAGE_COLOR,
                    int(self._width / 30),
                )

            rect = text.get_rect()
            rect.left = int(self._width * 0.10)
            rect.top = padding_y + draw_i * row_h
            self._renderer.blit(text, rect)

        # Hint footer
        hint_text = "[A/D] change   [W/S] select   [Enter] toggle/exit   [Esc] back   [C] random"
        hint = self._assets.render_custom(hint_text, GRID_COLOR, int(self._width / 50))
        self._renderer.blit(
            hint, hint.get_rect(center=(self._width / 2, self._height * 0.95))
        )

    def on_enter(self) -> None:
        """Called when entering settings."""
        self._selected_index = 0
