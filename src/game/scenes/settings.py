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

from game.scenes.base_scene import BaseScene
from game.services.assets import GameAssets
from game.settings import GameSettings
from game.constants import ARENA_COLOR, MESSAGE_COLOR, SCORE_COLOR, GRID_COLOR


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
        config=None,
    ):
        """Initialize the settings scene.

        Args:
            pygame_adapter: Pygame IO adapter
            renderer: Renderer for drawing
            width: Scene width
            height: Scene height
            assets: Game assets
            settings: Game settings
            config: Game config (for calculating grid size)
        """
        super().__init__(pygame_adapter, renderer, width, height)
        self._assets = assets
        self._settings = settings
        self._config = config
        self._selected_index = 0

    def update(self, dt_ms: float) -> Optional[str]:
        """Update settings logic.

        Args:
            dt_ms: Delta time in milliseconds

        Returns:
            Next scene name or None
        """
        # Update key holding state (this handles continuous changes)
        if self._settings.update_key_hold():
            # A value was updated by key holding
            current_field = self._settings.MENU_FIELDS[self._selected_index]
            self._apply_audio_setting_if_changed(current_field["key"])

        # Handle input
        for event in self._pygame_adapter.get_events():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()

            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_RETURN):
                    # Stop any ongoing key hold when leaving
                    self._settings.stop_key_hold()
                    return "menu"  # back to menu
                elif event.key in (pygame.K_DOWN, pygame.K_s):
                    # Stop key hold when changing selection
                    self._settings.stop_key_hold()
                    self._selected_index = (self._selected_index + 1) % len(
                        self._settings.MENU_FIELDS
                    )
                elif event.key in (pygame.K_UP, pygame.K_w):
                    # Stop key hold when changing selection
                    self._settings.stop_key_hold()
                    self._selected_index = (self._selected_index - 1) % len(
                        self._settings.MENU_FIELDS
                    )
                elif event.key in (pygame.K_LEFT, pygame.K_a):
                    # Start holding left
                    current_field = self._settings.MENU_FIELDS[self._selected_index]
                    self._settings.start_key_hold(current_field, -1)
                    # Apply audio settings immediately
                    self._apply_audio_setting_if_changed(current_field["key"])
                elif event.key in (pygame.K_RIGHT, pygame.K_d):
                    # Start holding right
                    current_field = self._settings.MENU_FIELDS[self._selected_index]
                    self._settings.start_key_hold(current_field, +1)
                    # Apply audio settings immediately
                    self._apply_audio_setting_if_changed(current_field["key"])

            elif event.type == pygame.KEYUP:
                # Stop holding when any left/right key is released
                if event.key in (pygame.K_LEFT, pygame.K_a, pygame.K_RIGHT, pygame.K_d):
                    self._settings.stop_key_hold()

        return None

    def _apply_audio_setting_if_changed(self, field_key: str) -> None:
        """Apply audio settings immediately when changed.

        Args:
            field_key: The key of the field that was changed
        """
        if field_key == "background_music":
            # Only control background music
            if self._settings.get("background_music"):
                pygame.mixer.music.unpause()
            else:
                pygame.mixer.music.pause()
        elif field_key == "sound_effects":
            # Control all sound effect channels
            if self._settings.get("sound_effects"):
                pygame.mixer.unpause()
            else:
                pygame.mixer.pause()

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

        # Spacing and scroll parameters
        row_h = int(self._height * 0.06)
        visible_rows = int(self._height * 0.70 // row_h)
        top_index = max(0, self._selected_index - visible_rows + 3)
        padding_y = int(self._height * 0.22)

        # Draw visible rows
        for draw_i, field_i in enumerate(
            range(top_index, len(self._settings.MENU_FIELDS))
        ):
            if draw_i >= visible_rows:
                break
            f = self._settings.MENU_FIELDS[field_i]
            val = self._settings.get(f["key"])

            # Calculate current grid size for display
            current_grid_size = 20  # default fallback
            if self._config:
                desired_cells = max(10, int(self._settings.get("cells_per_side")))
                current_grid_size = self._config.get_optimal_grid_size(desired_cells)

            formatted_val = self._settings.format_setting_value(
                f,
                val,
                self._width,
                current_grid_size,
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
        hint_text = "[A/D] change   [W/S] select   [Enter/Esc] back   [C] random colors"
        hint = self._assets.render_custom(hint_text, GRID_COLOR, int(self._width / 50))
        self._renderer.blit(
            hint, hint.get_rect(center=(self._width / 2, self._height * 0.95))
        )

    def on_enter(self) -> None:
        """Called when entering settings."""
        self._selected_index = 0
        # Make sure key hold is stopped when entering the scene
        self._settings.stop_key_hold()
