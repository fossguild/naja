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
from game.constants import ARENA_PRIMARY_COLOR, MESSAGE_COLOR, SCORE_COLOR, GRID_COLOR


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
        # total menu items = settings fields + "Reset to Default" button
        self._total_menu_items = len(self._settings.MENU_FIELDS) + 1
        # Hover state for warning tooltips
        self._hovered_warning_key = None
        self._warning_icon_rects = {}  # key -> rect for hover detection

    def update(self, dt_ms: float) -> Optional[str]:
        """Update settings logic.

        Args:
            dt_ms: Delta time in milliseconds

        Returns:
            Next scene name or None
        """
        # Update key holding state (this handles continuous changes)
        # Only update if not on "Reset to Default" button
        if self._selected_index < len(self._settings.MENU_FIELDS):
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
                if event.key == pygame.K_ESCAPE:
                    # Stop any ongoing key hold when leaving
                    self._settings.stop_key_hold()
                    return "menu"  # back to menu
                elif event.key == pygame.K_RETURN:
                    # Check if "Reset to Default" is selected
                    if self._selected_index == len(self._settings.MENU_FIELDS):
                        self._settings.reset_to_defaults()
                        self._settings.save_settings()
                        # Stay in settings to show the reset took effect
                    else:
                        # Regular return to menu
                        self._settings.stop_key_hold()
                        return "menu"
                elif event.key in (pygame.K_DOWN, pygame.K_s):
                    # Stop key hold when changing selection
                    self._settings.stop_key_hold()
                    self._selected_index = (
                        self._selected_index + 1
                    ) % self._total_menu_items
                elif event.key in (pygame.K_UP, pygame.K_w):
                    # Stop key hold when changing selection
                    self._settings.stop_key_hold()
                    self._selected_index = (
                        self._selected_index - 1
                    ) % self._total_menu_items
                elif event.key in (pygame.K_LEFT, pygame.K_a):
                    # Only handle left/right on settings fields, not on "Reset to Default"
                    if self._selected_index < len(self._settings.MENU_FIELDS):
                        current_field = self._settings.MENU_FIELDS[self._selected_index]
                        # Skip if setting is restricted (locked)
                        if not self._settings.is_setting_restricted(
                            current_field["key"]
                        ):
                            # Start holding left
                            self._settings.start_key_hold(current_field, -1)
                            # Apply audio settings immediately
                            self._apply_audio_setting_if_changed(current_field["key"])
                elif event.key in (pygame.K_RIGHT, pygame.K_d):
                    # Only handle left/right on settings fields, not on "Reset to Default"
                    if self._selected_index < len(self._settings.MENU_FIELDS):
                        current_field = self._settings.MENU_FIELDS[self._selected_index]
                        # Skip if setting is restricted (locked)
                        if not self._settings.is_setting_restricted(
                            current_field["key"]
                        ):
                            # Start holding right
                            self._settings.start_key_hold(current_field, +1)
                            # Apply audio settings immediately
                            self._apply_audio_setting_if_changed(current_field["key"])
                elif event.key == pygame.K_c:
                    # Randomize snake colors
                    self._settings.randomize_snake_colors()

            elif event.type == pygame.KEYUP:
                # Stop holding when any left/right key is released
                if event.key in (pygame.K_LEFT, pygame.K_a, pygame.K_RIGHT, pygame.K_d):
                    self._settings.stop_key_hold()

        # Track mouse hover for warning tooltips
        mouse_pos = pygame.mouse.get_pos()
        self._hovered_warning_key = None
        for key, rect in self._warning_icon_rects.items():
            if rect.collidepoint(mouse_pos):
                self._hovered_warning_key = key
                break

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
        """Render the settings screen with categorized layout."""
        # Clear screen
        self._renderer.fill(ARENA_PRIMARY_COLOR)

        # Clear warning icon rects for fresh hover detection
        self._warning_icon_rects.clear()

        # Draw title
        title = self._assets.render_custom(
            "Settings", MESSAGE_COLOR, int(self._width / 12)
        )
        title_rect = title.get_rect(center=(self._width / 2, self._height / 10))
        self._renderer.blit(title, title_rect)

        # Layout parameters
        row_h = int(self._height * 0.055)
        category_h = int(self._height * 0.07)
        padding_y = int(self._height * 0.20)
        left_margin = int(self._width * 0.15)
        category_indent = int(self._width * 0.05)

        # Calculate available height for content
        content_start_y = padding_y
        content_end_y = int(self._height * 0.88)

        # Calculate scroll offset to keep selected item visible
        item_height_avg = row_h
        scroll_offset = max(0, (self._selected_index - 3) * item_height_avg)

        current_y = padding_y - scroll_offset
        current_category = None

        # Draw settings grouped by category
        for field_i, f in enumerate(self._settings.MENU_FIELDS):
            # Draw category header if this is a new category
            if f.get("category") != current_category:
                current_category = f.get("category", "Other")

                # Add spacing before category (except first)
                if field_i > 0:
                    current_y += int(self._height * 0.03)

                # Draw category header only if visible
                if content_start_y - category_h <= current_y <= content_end_y:
                    category_text = self._assets.render_custom(
                        f"─── {current_category} ───",
                        (180, 180, 180),
                        int(self._width / 32),
                    )
                    category_rect = category_text.get_rect()
                    category_rect.left = left_margin - category_indent
                    category_rect.top = current_y
                    self._renderer.blit(category_text, category_rect)

                current_y += category_h

            # Draw setting field only if visible
            if content_start_y - row_h <= current_y <= content_end_y:
                val = self._settings.get(f["key"])

                # Calculate current grid size for display
                current_grid_size = 20
                if self._config:
                    desired_cells = max(10, int(self._settings.get("cells_per_side")))
                    current_grid_size = self._config.get_optimal_grid_size(
                        desired_cells
                    )

                formatted_val = self._settings.format_setting_value(
                    f,
                    val,
                    self._width,
                    current_grid_size,
                )

                # Check if setting is restricted
                is_restricted = self._settings.is_setting_restricted(f["key"])

                # Highlight selected item (dim color if restricted)
                if is_restricted:
                    # Restricted settings shown in orange/amber
                    color = (
                        (255, 180, 60)
                        if field_i == self._selected_index
                        else (180, 130, 60)
                    )
                else:
                    color = (
                        SCORE_COLOR
                        if field_i == self._selected_index
                        else MESSAGE_COLOR
                    )
                text = self._assets.render_custom(
                    f"{f['label']}: {formatted_val}",
                    color,
                    int(self._width / 32),
                )
                rect = text.get_rect()
                rect.left = left_margin
                rect.top = current_y
                self._renderer.blit(text, rect)

                # Draw warning indicator if restricted
                if is_restricted:
                    # Draw [!] warning icon
                    warning_icon = self._assets.render_custom(
                        "[!]",
                        (255, 200, 50),  # Amber/yellow warning color
                        int(self._width / 32),
                    )
                    icon_rect = warning_icon.get_rect()
                    icon_rect.left = rect.right + 8
                    icon_rect.centery = rect.centery
                    self._renderer.blit(warning_icon, icon_rect)
                    # Store rect for hover detection
                    self._warning_icon_rects[f["key"]] = icon_rect

                    # Draw LOCKED label
                    locked_text = self._assets.render_custom(
                        "LOCKED",
                        (180, 80, 80),  # Red-ish color
                        int(self._width / 45),
                    )
                    locked_rect = locked_text.get_rect()
                    locked_rect.left = icon_rect.right + 8
                    locked_rect.centery = rect.centery
                    self._renderer.blit(locked_text, locked_rect)

            current_y += row_h

        # Draw "Reset to Default" button
        current_y += int(self._height * 0.04)
        reset_index = len(self._settings.MENU_FIELDS)

        # Only draw if visible
        if content_start_y - row_h <= current_y <= content_end_y:
            reset_text = self._assets.render_custom(
                "──  Reset to Default  ──",
                SCORE_COLOR if self._selected_index == reset_index else (200, 100, 100),
                int(self._width / 32),
            )
            reset_rect = reset_text.get_rect()
            reset_rect.left = left_margin - category_indent
            reset_rect.top = current_y
            self._renderer.blit(reset_text, reset_rect)

        # Hint footer
        hint_text = "[A/D] change   [W/S] select   [Enter/Esc] back   [C] random colors"
        hint = self._assets.render_custom(hint_text, GRID_COLOR, int(self._width / 50))
        self._renderer.blit(
            hint, hint.get_rect(center=(self._width / 2, self._height * 0.95))
        )

        # Draw hover tooltip for restricted settings
        if (
            self._hovered_warning_key
            and self._hovered_warning_key in self._warning_icon_rects
        ):
            reason = self._settings.get_restriction_reason(self._hovered_warning_key)
            if reason:
                # Get mouse position for tooltip placement
                mouse_pos = pygame.mouse.get_pos()

                # Render tooltip text
                tooltip_text = f"Locked for AutoPlay: {reason}"
                tooltip_surface = self._assets.render_custom(
                    tooltip_text,
                    (255, 255, 255),
                    int(self._width / 45),
                )
                tooltip_rect = tooltip_surface.get_rect()

                # Position tooltip near mouse, with padding
                padding = 8
                tooltip_rect.left = mouse_pos[0] + 15
                tooltip_rect.top = mouse_pos[1] - tooltip_rect.height - 5

                # Keep tooltip on screen
                if tooltip_rect.right > self._width - padding:
                    tooltip_rect.right = self._width - padding
                if tooltip_rect.top < padding:
                    tooltip_rect.top = mouse_pos[1] + 20

                # Draw tooltip background
                bg_rect = tooltip_rect.inflate(16, 10)
                pygame.draw.rect(
                    self._renderer._surface, (40, 40, 40), bg_rect, border_radius=4
                )
                pygame.draw.rect(
                    self._renderer._surface,
                    (255, 180, 50),
                    bg_rect,
                    width=2,
                    border_radius=4,
                )

                # Draw tooltip text
                self._renderer.blit(tooltip_surface, tooltip_rect)

    def on_enter(self) -> None:
        """Called when entering settings."""
        self._selected_index = 0
        # Make sure key hold is stopped when entering the scene
        self._settings.stop_key_hold()
