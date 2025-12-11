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
from game.constants import (
    ARENA_PRIMARY_COLOR,
    MESSAGE_COLOR_LIGHT,
    MESSAGE_COLOR_DARK,
    SCORE_COLOR,
)


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
        # track which sections are collapsed
        self._collapsed_sections = set()
        # initialize collapsed sections from field definitions (only once)
        for field in self._settings.MENU_FIELDS:
            if field["type"] == "section" and field.get("collapsed", False):
                self._collapsed_sections.add(field["key"])
        # total menu items = visible settings fields + "Reset to Default" button
        self._total_menu_items = len(self._settings.MENU_FIELDS) + 1
        # hover state for warning tooltips
        self._hovered_warning_key = None
        self._warning_icon_rects = {}  # key -> rect for hover detection
        self._item_rects = []  # rects for mouse interaction
        # key repeat tracking for smooth scrolling
        self._key_down_pressed = False
        self._key_up_pressed = False
        self._key_repeat_timer = 0.0
        self._key_repeat_initial_delay = 300.0  # ms before repeat starts
        self._key_repeat_interval = 80.0  # ms between repeats

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
        if self._selected_index > len(visible_fields):
            self._selected_index = len(visible_fields)
        if self._selected_index < 0:
            self._selected_index = 0

        # Handle key repeat for smooth scrolling
        if self._key_down_pressed or self._key_up_pressed:
            self._key_repeat_timer += dt_ms
            # check if we should trigger a repeat
            should_repeat = False
            if self._key_repeat_timer >= self._key_repeat_initial_delay:
                # after initial delay, repeat at interval
                if (
                    self._key_repeat_timer
                    >= self._key_repeat_initial_delay + self._key_repeat_interval
                ):
                    should_repeat = True
                    # reset timer but keep the "credit" for smooth repeating
                    self._key_repeat_timer = self._key_repeat_initial_delay

            if should_repeat:
                total_items = len(visible_fields) + 1
                if self._key_down_pressed:
                    self._selected_index = (self._selected_index + 1) % total_items
                elif self._key_up_pressed:
                    self._selected_index = (self._selected_index - 1) % total_items

        # Update key holding state (this handles continuous changes)
        # Only update if not on "Reset to Default" button
        if self._selected_index < len(visible_fields):
            current_field = visible_fields[self._selected_index]
            # only update if not a section
            if current_field["type"] != "section" and self._settings.update_key_hold():
                # A value was updated by key holding
                self._apply_audio_setting_if_changed(current_field["key"])

        # Handle input
        for event in self._pygame_adapter.get_events():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()

            # Mouse Interaction Logic
            elif event.type == pygame.MOUSEBUTTONDOWN:
                total_items = len(visible_fields) + 1

                # Scroll Wheel: Maps directly to selection index for consistency
                if event.button == 4:  # Scroll Up
                    self._selected_index = (self._selected_index - 1) % total_items
                elif event.button == 5:  # Scroll Down
                    self._selected_index = (self._selected_index + 1) % total_items

                # Clicks: Check against rects stored in render
                elif event.button in (1, 3):  # Left(1) or Right(3) Click
                    mouse_pos = pygame.mouse.get_pos()
                    for rect, idx in self._item_rects:
                        if rect.collidepoint(mouse_pos):
                            # Move selection to clicked item
                            self._selected_index = idx

                            # Handle interaction
                            if idx == len(visible_fields):  # Reset Button
                                if event.button == 1:
                                    self._settings.reset_to_defaults()
                                    self._settings.save_settings()
                            else:  # Regular Field or Section
                                field = visible_fields[idx]

                                if field["type"] == "section" and event.button == 1:
                                    self._toggle_section(field["key"])
                                elif field["type"] != "section":
                                    if not self._settings.is_setting_restricted(
                                        field["key"]
                                    ):
                                        # Left click increases, Right click decreases
                                        change = 1 if event.button == 1 else -1
                                        self._settings.start_key_hold(field, change)
                                        self._settings.stop_key_hold()  # Immediate single click
                                        self._apply_audio_setting_if_changed(
                                            field["key"]
                                        )

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    # Stop any ongoing key hold when leaving
                    self._settings.stop_key_hold()
                    # Reset key repeat state
                    self._key_down_pressed = False
                    self._key_up_pressed = False
                    self._key_repeat_timer = 0.0
                    return "menu"  # back to menu
                elif event.key == pygame.K_RETURN:
                    # Check if "Reset to Default" is selected
                    if self._selected_index == len(visible_fields):
                        self._settings.reset_to_defaults()
                        self._settings.save_settings()
                        # if background music was off, return music
                        if not pygame.mixer.music.get_busy():
                            pygame.mixer.music.unpause()
                        # Stay in settings to show the reset took effect
                    elif self._selected_index < len(visible_fields):
                        # toggle section if selected field is a section
                        current_field = visible_fields[self._selected_index]
                        print(
                            f"[DEBUG] Enter pressed on field: {current_field.get('label')} (type: {current_field.get('type')})"
                        )
                        if current_field["type"] == "section":
                            print(f"[DEBUG] Toggling section: {current_field['key']}")
                            self._toggle_section(current_field["key"])
                            print(
                                f"[DEBUG] Collapsed sections: {self._collapsed_sections}"
                            )
                        else:
                            # Regular field - return to menu
                            self._settings.stop_key_hold()
                            return "menu"
                elif event.key in (pygame.K_DOWN, pygame.K_s):
                    # Stop key hold when changing selection
                    self._settings.stop_key_hold()
                    # navigate through visible fields + reset button
                    total_items = len(visible_fields) + 1
                    self._selected_index = (self._selected_index + 1) % total_items
                    # mark key as pressed and reset timer for repeat
                    self._key_down_pressed = True
                    self._key_up_pressed = False
                    self._key_repeat_timer = 0.0
                elif event.key in (pygame.K_UP, pygame.K_w):
                    # Stop key hold when changing selection
                    self._settings.stop_key_hold()
                    # navigate through visible fields + reset button
                    total_items = len(visible_fields) + 1
                    self._selected_index = (self._selected_index - 1) % total_items
                    # mark key as pressed and reset timer for repeat
                    self._key_up_pressed = True
                    self._key_down_pressed = False
                    self._key_repeat_timer = 0.0
                elif event.key in (pygame.K_LEFT, pygame.K_a):
                    # Only handle left/right on settings fields, not on "Reset to Default"
                    if self._selected_index < len(visible_fields):
                        current_field = visible_fields[self._selected_index]
                        # Skip if field is a section or setting is restricted (locked)
                        if current_field[
                            "type"
                        ] != "section" and not self._settings.is_setting_restricted(
                            current_field["key"]
                        ):
                            # Start holding left
                            self._settings.start_key_hold(current_field, -1)
                            # Apply audio settings immediately
                            self._apply_audio_setting_if_changed(current_field["key"])
                elif event.key in (pygame.K_RIGHT, pygame.K_d):
                    # Only handle left/right on settings fields, not on "Reset to Default"
                    if self._selected_index < len(visible_fields):
                        current_field = visible_fields[self._selected_index]
                        # Skip if field is a section or setting is restricted (locked)
                        if current_field[
                            "type"
                        ] != "section" and not self._settings.is_setting_restricted(
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
                # Stop key repeat when up/down keys are released
                if event.key in (pygame.K_DOWN, pygame.K_s):
                    self._key_down_pressed = False
                    self._key_repeat_timer = 0.0
                elif event.key in (pygame.K_UP, pygame.K_w):
                    self._key_up_pressed = False
                    self._key_repeat_timer = 0.0

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

        # Clear interactive rects
        self._item_rects = []

        # Draw title
        title = self._assets.render_custom(
            "Settings", MESSAGE_COLOR_LIGHT, int(self._width / 12)
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

        # Get visible fields (respecting section collapse state)
        visible_fields = self._get_visible_fields()

        # Get mouse pos for hover effect
        mouse_pos = pygame.mouse.get_pos()

        # Draw settings grouped by category
        for field_i, f in enumerate(visible_fields):
            # skip category headers for section headers and their children
            is_section_child = f.get("parent_section") is not None
            is_section = f.get("type") == "section"

            # Draw category header if this is a new category (but not for sections or section children)
            if (
                not is_section
                and not is_section_child
                and f.get("category") != current_category
            ):
                current_category = f.get("category", "Other")

                # Add spacing before category (except first)
                if field_i > 0:
                    current_y += int(self._height * 0.03)

                # Draw category header only if visible
                if content_start_y - category_h <= current_y <= content_end_y:
                    category_text = self._assets.render_custom(
                        f"─── {current_category} ───",
                        MESSAGE_COLOR_LIGHT,
                        int(self._width / 32),
                    )
                    category_rect = category_text.get_rect()
                    category_rect.left = left_margin - category_indent
                    category_rect.top = current_y
                    self._renderer.blit(category_text, category_rect)

                current_y += category_h

            # Draw setting field only if visible
            if content_start_y - row_h <= current_y <= content_end_y:
                # Rect for hit detection (width extends to cover the row)
                hit_rect = pygame.Rect(
                    left_margin - category_indent, current_y, self._width * 0.7, row_h
                )
                self._item_rects.append((hit_rect, field_i))

                is_mouse_hover = hit_rect.collidepoint(mouse_pos)

                # handle section headers specially
                if f["type"] == "section":
                    # section headers get a collapse indicator
                    is_expanded = f["key"] not in self._collapsed_sections
                    indicator = "v" if is_expanded else ">"
                    label_text = f"{indicator} {f['label']}"

                    # make section headers slightly larger
                    color = (
                        MESSAGE_COLOR_DARK
                        if (field_i == self._selected_index or is_mouse_hover)
                        else MESSAGE_COLOR_LIGHT
                    )
                    text = self._assets.render_custom(
                        label_text,
                        color,
                        int(self._width / 28),
                    )
                    rect = text.get_rect()
                    rect.left = left_margin - category_indent
                    rect.top = current_y
                    self._renderer.blit(text, rect)
                else:
                    # regular fields
                    val = self._settings.get(f["key"])

                    # Calculate current grid size for display
                    current_grid_size = 20
                    if self._config:
                        desired_cells = max(
                            10, int(self._settings.get("cells_per_side"))
                        )
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
                            if (field_i == self._selected_index or is_mouse_hover)
                            else (180, 130, 60)
                        )
                    else:
                        color = (
                            MESSAGE_COLOR_LIGHT
                            if (field_i == self._selected_index or is_mouse_hover)
                            else MESSAGE_COLOR_DARK
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
        reset_index = len(visible_fields)

        # Only draw if visible
        if content_start_y - row_h <= current_y <= content_end_y:
            reset_rect_hit = pygame.Rect(
                left_margin - category_indent, current_y, self._width * 0.7, row_h
            )
            self._item_rects.append((reset_rect_hit, reset_index))
            is_reset_hover = reset_rect_hit.collidepoint(mouse_pos)

            reset_color = (200, 100, 100)
            if self._selected_index == reset_index or is_reset_hover:
                reset_color = SCORE_COLOR

            reset_text = self._assets.render_custom(
                "──  Reset to Default  ──",
                (
                    MESSAGE_COLOR_LIGHT
                    if self._selected_index == reset_index
                    else reset_color
                ),
                int(self._width / 32),
            )
            reset_rect = reset_text.get_rect()
            reset_rect.left = left_margin - category_indent
            reset_rect.top = current_y
            self._renderer.blit(reset_text, reset_rect)

        # Hint footer
        hint_text = "[A/D/Click] change   [W/S/Scroll] select   [Enter] toggle/exit   [Esc] back"
        hint = self._assets.render_custom(
            hint_text, MESSAGE_COLOR_LIGHT, int(self._width / 50)
        )
        self._renderer.blit(
            hint, hint.get_rect(center=(self._width / 2, self._height * 0.95))
        )

        # Seizure warning for rainbow color in AutoPlay mode
        from game.game_modes_registry import AUTOPLAY_MODE_NAME

        is_autoplay = self._settings.get_game_mode() == AUTOPLAY_MODE_NAME
        is_rainbow = "rainbow" in str(self._settings.get("snake_color_palette")).lower()
        if is_autoplay and is_rainbow:
            # Draw seizure warning banner
            warning_text = (
                "[!] SEIZURE WARNING: Rainbow colors + high speed may cause discomfort"
            )
            warning_surface = self._assets.render_custom(
                warning_text,
                (255, 100, 100),  # Red warning color
                int(self._width / 45),
            )
            warning_rect = warning_surface.get_rect(
                center=(self._width / 2, self._height * 0.90)
            )
            # Draw background for visibility
            bg_rect = warning_rect.inflate(20, 8)
            self._renderer.draw_rect((40, 20, 20), bg_rect)
            self._renderer.blit(warning_surface, warning_rect)

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
                self._renderer.draw_rect((40, 40, 40), bg_rect)

                # Draw tooltip text
                self._renderer.blit(tooltip_surface, tooltip_rect)

    def on_enter(self) -> None:
        """Called when entering settings."""
        self._selected_index = 0
        # Make sure key hold is stopped when entering the scene
        self._settings.stop_key_hold()
