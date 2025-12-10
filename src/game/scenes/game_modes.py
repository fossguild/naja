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

"""Game modes menu scene."""

from __future__ import annotations

import pygame
import random
from typing import Optional

from game.scenes.base_scene import BaseScene
from game.services.assets import GameAssets
from game.settings import GameSettings
from game.constants import ARENA_PRIMARY_COLOR, MESSAGE_COLOR_LIGHT, MESSAGE_COLOR_DARK
from game.game_modes_registry import (
    ACTUAL_GAME_MODES,
    CLASSIC_MODE_NAME,
    RANDOM_MODE_INDEX,
    RANDOM_MODE_LABEL,
)

# global variable to store selected game mode
_selected_game_mode = 0  # defaults to Classic


def get_selected_game_mode() -> int:
    """Get the currently selected game mode.

    Returns:
        Index of selected game mode (0=Classic, 1=Random)
    """
    return _selected_game_mode


def set_selected_game_mode(mode: int) -> None:
    """Set the selected game mode.

    Args:
        mode: Index of game mode to select (actual modes + random option)
    """
    global _selected_game_mode
    max_index = RANDOM_MODE_INDEX
    _selected_game_mode = max(0, min(mode, max_index))


def get_resolved_game_mode() -> str:
    """Get the actual game mode to play.

    If Random is selected, picks a random actual game mode.
    Otherwise returns the selected mode name.

    Returns:
        Name of the actual game mode to play
    """
    if _selected_game_mode == RANDOM_MODE_INDEX:  # Random mode
        return random.choice([mode["name"] for mode in ACTUAL_GAME_MODES])
    elif _selected_game_mode < len(ACTUAL_GAME_MODES):
        return ACTUAL_GAME_MODES[_selected_game_mode]["name"]
    else:
        return CLASSIC_MODE_NAME


def get_display_mode_name() -> str:
    """Get the display name for the selected mode.

    Returns:
        Display name showing what will be played
    """
    if _selected_game_mode == RANDOM_MODE_INDEX:
        return "Random Mode"
    elif _selected_game_mode < len(ACTUAL_GAME_MODES):
        return ACTUAL_GAME_MODES[_selected_game_mode]["name"]
    return CLASSIC_MODE_NAME


class GameModesScene(BaseScene):
    """Game modes selection menu."""

    def __init__(
        self,
        pygame_adapter,
        renderer,
        width: int,
        height: int,
        assets: GameAssets,
        settings: GameSettings,
    ):
        """Initialize the game modes scene.

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
        self._menu_items = [
            *[mode["name"] for mode in ACTUAL_GAME_MODES],
            RANDOM_MODE_LABEL,
        ]
        self._assets.snake_icons = [
            self._assets.snake_icons_left,
            self._assets.snake_icons_right,
        ]
        self._showing_info_modal = False  # track if modal is open
        self._info_modal_index = -1  # which mode's info to show
        self._modal_selected_button = 0  # 0 = Apply, 1 = Cancel

    def update(self, dt_ms: float) -> Optional[str]:
        """Update game modes menu logic."""
        # Handle input
        for event in self._pygame_adapter.get_events():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()

            elif event.type == pygame.KEYDOWN:
                # if modal is open, handle modal navigation
                if self._showing_info_modal:
                    if event.key == pygame.K_ESCAPE:
                        # close modal without applying
                        self._showing_info_modal = False
                        self._info_modal_index = -1
                        self._modal_selected_button = 0
                        continue
                    elif event.key in (pygame.K_LEFT, pygame.K_a):
                        self._modal_selected_button = 0  # Apply
                    elif event.key in (pygame.K_RIGHT, pygame.K_d):
                        self._modal_selected_button = 1  # Cancel
                    elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        if self._modal_selected_button == 0:  # Apply
                            # save the selected game mode
                            set_selected_game_mode(self._info_modal_index)

                            # Get the resolved mode name and set on settings for restriction tracking
                            resolved_mode = get_resolved_game_mode()
                            self._settings.set_game_mode(resolved_mode)

                            # if Classic Snake Game is selected, reset settings to default
                            if self._info_modal_index == 0:  # Classic mode
                                self._settings.reset_to_defaults()
                                self._settings.save_settings()
                            elif self._info_modal_index == 1:  # Random
                                self._settings.reset_to_defaults()
                                self._settings.save_settings()
                            elif self._info_modal_index == 2:  # Head-Tail Swap mode
                                self._settings.reset_to_defaults()
                                self._settings.save_settings()

                            # close modal and go back to main menu
                            self._showing_info_modal = False
                            self._info_modal_index = -1
                            self._modal_selected_button = 0
                            return "menu"
                        else:  # Cancel
                            # close modal without applying
                            self._showing_info_modal = False
                            self._info_modal_index = -1
                            self._modal_selected_button = 0
                    continue

                # normal navigation when modal is closed
                if event.key in (pygame.K_UP, pygame.K_w):
                    self._selected_index = (self._selected_index - 1) % len(
                        self._menu_items
                    )
                elif event.key in (pygame.K_DOWN, pygame.K_s):
                    self._selected_index = (self._selected_index + 1) % len(
                        self._menu_items
                    )
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    # show modal for actual game modes
                    if self._selected_index < len(ACTUAL_GAME_MODES):
                        self._showing_info_modal = True
                        self._info_modal_index = self._selected_index
                        self._modal_selected_button = 0
                    # Random mode doesn't need modal, just apply directly
                    elif self._selected_index == RANDOM_MODE_INDEX:
                        set_selected_game_mode(self._selected_index)
                        resolved_mode = get_resolved_game_mode()
                        self._settings.set_game_mode(resolved_mode)
                        self._settings.reset_to_defaults()
                        self._settings.save_settings()
                        return "menu"
                elif event.key == pygame.K_ESCAPE:
                    # go back to main menu
                    return "menu"

            elif event.type == pygame.MOUSEMOTION:
                # handle mouse hover
                mouse_pos = event.pos
                pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)

                # if modal is open, check hover over buttons
                if self._showing_info_modal:
                    apply_rect, cancel_rect = self._get_modal_button_rects()
                    if apply_rect and apply_rect.collidepoint(mouse_pos):
                        pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)
                        self._modal_selected_button = 0
                    elif cancel_rect and cancel_rect.collidepoint(mouse_pos):
                        pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)
                        self._modal_selected_button = 1

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # handle left mouse click
                mouse_pos = event.pos

                # if modal is open, check button clicks
                if self._showing_info_modal:
                    apply_rect, cancel_rect = self._get_modal_button_rects()

                    if apply_rect and apply_rect.collidepoint(mouse_pos):
                        # Apply button clicked
                        set_selected_game_mode(self._info_modal_index)
                        resolved_mode = get_resolved_game_mode()
                        self._settings.set_game_mode(resolved_mode)

                        if self._info_modal_index == 0:  # Classic mode
                            self._settings.reset_to_defaults()
                            self._settings.save_settings()
                        elif self._info_modal_index == 1:  # Random
                            self._settings.reset_to_defaults()
                            self._settings.save_settings()
                        elif self._info_modal_index == 2:  # Head-Tail Swap mode
                            self._settings.reset_to_defaults()
                            self._settings.save_settings()

                        self._showing_info_modal = False
                        self._info_modal_index = -1
                        self._modal_selected_button = 0
                        return "menu"

                    elif cancel_rect and cancel_rect.collidepoint(mouse_pos):
                        # Cancel button clicked
                        self._showing_info_modal = False
                        self._info_modal_index = -1
                        self._modal_selected_button = 0

                    else:
                        # check if clicking outside modal to close
                        modal_rect = self._get_modal_rect()
                        if modal_rect and not modal_rect.collidepoint(mouse_pos):
                            self._showing_info_modal = False
                            self._info_modal_index = -1
                            self._modal_selected_button = 0
                    continue

        return None

    def render(self) -> None:
        """Render the game modes menu with proper spacing like settings."""
        # Clear screen
        self._renderer.fill(ARENA_PRIMARY_COLOR)

        # Draw title
        title = self._assets.render_custom(
            "Game Modes", MESSAGE_COLOR_LIGHT, int(self._width / 12)
        )
        title_rect = title.get_rect(center=(self._width / 2, self._height / 10))
        self._renderer.blit(title, title_rect)

        # Layout parameters with scrolling
        row_h = int(self._height * 0.10)
        padding_y = int(self._height * 0.25)

        # Define content boundaries
        content_start_y = padding_y
        content_end_y = int(self._height * 0.88)

        # Calculate if all items fit without scrolling
        # Total height needed = number of items * row height
        total_items_height = len(self._menu_items) * row_h
        available_height = content_end_y - padding_y

        # Only scroll if items don't fit
        if total_items_height > available_height:
            scroll_offset = max(0, (self._selected_index - 2) * row_h)
        else:
            scroll_offset = 0

        current_y = padding_y - scroll_offset

        # Draw menu items with scrolling
        for i, item in enumerate(self._menu_items):
            # Only draw if in visible range
            if content_start_y <= current_y <= content_end_y:
                color = (
                    MESSAGE_COLOR_LIGHT
                    if i == self._selected_index
                    else MESSAGE_COLOR_DARK
                )

                # add arrow indicator if this mode is selected (confirmed)
                display_text = item
                if i == get_selected_game_mode():
                    display_text = f">> {item} <<"

                # Use consistent font size, centered
                text = self._assets.render_custom(
                    display_text, color, int(self._width / 25)
                )
                rect = text.get_rect(center=(self._width / 2, current_y))
                self._renderer.blit(text, rect)

                # Draw description for currently navigated mode (centered, wrapped)
                if i == self._selected_index:
                    # Snake icons
                    img_size = 20
                    img_y_center = current_y

                    # Left img
                    left_img = self._assets.snake_icons_left
                    left_img_x = rect.left - 20 - img_size
                    left_rect = left_img.get_rect(
                        center=(left_img_x + (img_size / 2), img_y_center)
                    )
                    self._renderer.blit(left_img, left_rect)

                    # Right img
                    right_img = self._assets.snake_icons_right
                    right_img_x = rect.right + 20
                    right_rect = right_img.get_rect(
                        center=(right_img_x + (img_size / 2), img_y_center)
                    )
                    self._renderer.blit(right_img, right_rect)

                    description = self._get_description_for_index(i)
                    if description:
                        desc_y = current_y + int(self._height * 0.04)
                        if content_start_y <= desc_y <= content_end_y:
                            # Wrap text to fit screen width (85% of screen)
                            wrapped_lines = self._wrap_text(
                                description,
                                int(self._width * 0.85),
                                int(self._width / 50),
                            )
                            for line_i, line in enumerate(wrapped_lines):
                                line_y = desc_y + line_i * int(self._height * 0.025)
                                desc_text = self._assets.render_custom(
                                    line, (120, 120, 120), int(self._width / 50)
                                )
                                desc_rect = desc_text.get_rect(
                                    center=(self._width / 2, line_y)
                                )
                                self._renderer.blit(desc_text, desc_rect)

            current_y += row_h

        # Draw hint footer (always at fixed bottom position)
        hint_text = self._assets.render_custom(
            "Press ESC to go back", MESSAGE_COLOR_LIGHT, int(self._width / 50)
        )
        hint_rect = hint_text.get_rect(center=(self._width / 2, self._height * 0.95))
        self._renderer.blit(hint_text, hint_rect)

        # Draw floating modal if open
        if self._showing_info_modal and 0 <= self._info_modal_index < len(
            ACTUAL_GAME_MODES
        ):
            modal_rect = self._get_modal_rect()
            mode_info = ACTUAL_GAME_MODES[self._info_modal_index]

            # draw semi-transparent overlay
            overlay = pygame.Surface((self._width, self._height))
            overlay.set_alpha(180)
            overlay.fill((0, 0, 0))
            self._renderer.blit(overlay, (0, 0))

            # draw modal background using renderer's draw_rect
            self._renderer.draw_rect((40, 40, 50), modal_rect)  # filled background
            self._renderer.draw_rect((100, 150, 200), modal_rect, 3)  # border

            # draw mode name as title
            title_text = self._assets.render_custom(
                mode_info["name"], (100, 200, 255), int(self._width / 20)
            )
            title_rect = title_text.get_rect(
                center=(modal_rect.centerx, modal_rect.top + 40)
            )
            self._renderer.blit(title_text, title_rect)

            # draw detailed info with word wrap
            detailed_info = mode_info.get(
                "detailed_info", "No detailed information available."
            )
            wrapped_lines = self._wrap_text(
                detailed_info,
                int(modal_rect.width * 0.9),
                int(self._width / 35),
            )

            text_y = modal_rect.top + 100
            line_height = int(self._height * 0.04)
            for line in wrapped_lines:
                line_text = self._assets.render_custom(
                    line, (220, 220, 220), int(self._width / 35)
                )
                line_rect = line_text.get_rect(center=(modal_rect.centerx, text_y))
                self._renderer.blit(line_text, line_rect)
                text_y += line_height

            # draw Apply and Cancel buttons
            apply_rect, cancel_rect = self._get_modal_button_rects()

            # Apply button
            apply_color = (
                (80, 180, 100) if self._modal_selected_button == 0 else (60, 140, 80)
            )
            self._renderer.draw_rect(apply_color, apply_rect)
            self._renderer.draw_rect((150, 255, 150), apply_rect, 2)

            apply_text = self._assets.render_custom(
                "Apply", (255, 255, 255), int(self._width / 30)
            )
            apply_text_rect = apply_text.get_rect(center=apply_rect.center)
            self._renderer.blit(apply_text, apply_text_rect)

            # Cancel button
            cancel_color = (
                (180, 80, 80) if self._modal_selected_button == 1 else (140, 60, 60)
            )
            self._renderer.draw_rect(cancel_color, cancel_rect)
            self._renderer.draw_rect((255, 150, 150), cancel_rect, 2)

            cancel_text = self._assets.render_custom(
                "Cancel", (255, 255, 255), int(self._width / 30)
            )
            cancel_text_rect = cancel_text.get_rect(center=cancel_rect.center)
            self._renderer.blit(cancel_text, cancel_text_rect)

    def on_enter(self) -> None:
        """Called when entering game modes menu."""
        # start with cursor on currently selected game mode
        self._selected_index = get_selected_game_mode()

        # play menu music when entering game modes menu
        if self._settings.get("background_music"):
            try:
                import pygame
                from game.services.audio_service import AudioService
                from game.services.assets import GameAssets

                # only reload if menu music is not already playing
                if GameAssets._current_music_track != "assets/sound/menu.mp3":
                    pygame.mixer.music.load("assets/sound/menu.mp3")
                    pygame.mixer.music.play(-1)  # loop
                    GameAssets._current_music_track = "assets/sound/menu.mp3"
                    AudioService._current_music_track = "assets/sound/menu.mp3"
            except Exception:
                pass

    def _get_description_for_index(self, index: int) -> Optional[str]:
        """Get the friendly description for a menu entry."""
        if index < len(ACTUAL_GAME_MODES):
            return ACTUAL_GAME_MODES[index]["description"]
        elif index == RANDOM_MODE_INDEX:
            return "Randomly selects one of the unlocked game modes."
        return None

    def _get_modal_rect(self) -> Optional[pygame.Rect]:
        """Calculate bounding box for the info modal.

        Returns:
            pygame.Rect representing the modal area
        """
        # modal is centered and takes up 70% of screen
        modal_width = int(self._width * 0.7)
        modal_height = int(self._height * 0.6)
        modal_x = (self._width - modal_width) // 2
        modal_y = (self._height - modal_height) // 2

        return pygame.Rect(modal_x, modal_y, modal_width, modal_height)

    def _get_modal_button_rects(self) -> tuple[pygame.Rect, pygame.Rect]:
        """Calculate bounding boxes for Apply and Cancel buttons.

        Returns:
            Tuple of (apply_rect, cancel_rect)
        """
        modal_rect = self._get_modal_rect()

        button_width = int(modal_rect.width * 0.35)
        button_height = 50
        button_y = modal_rect.bottom - 80

        # Apply button on the left
        apply_x = modal_rect.centerx - button_width - 20
        apply_rect = pygame.Rect(apply_x, button_y, button_width, button_height)

        # Cancel button on the right
        cancel_x = modal_rect.centerx + 20
        cancel_rect = pygame.Rect(cancel_x, button_y, button_width, button_height)

        return apply_rect, cancel_rect

    def _wrap_text(self, text: str, max_width: int, font_size: int) -> list[str]:
        """Wrap text to fit within max_width."""
        import pygame

        font_path = "assets/font/GetVoIP-Grotesque.ttf"
        try:
            font = pygame.font.Font(font_path, font_size)
        except Exception:
            font = pygame.font.Font(None, font_size)

        # If text fits in one line, return as is
        test_surface = font.render(text, True, (255, 255, 255))
        if test_surface.get_width() <= max_width:
            return [text]

        # Split text into words and wrap
        words = text.split()
        lines = []
        current_line = []

        for word in words:
            test_line = " ".join(current_line + [word])
            test_surface = font.render(test_line, True, (255, 255, 255))

            if test_surface.get_width() <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(" ".join(current_line))
                    current_line = [word]
                else:
                    # Single word is too long, add it anyway
                    lines.append(word)

        if current_line:
            lines.append(" ".join(current_line))

        return lines
