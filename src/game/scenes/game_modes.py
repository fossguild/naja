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
from game.constants import ARENA_PRIMARY_COLOR, MESSAGE_COLOR, SCORE_COLOR
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
            "──  Back to Menu  ──",
            *[mode["name"] for mode in ACTUAL_GAME_MODES],
            RANDOM_MODE_LABEL,
        ]

    def update(self, dt_ms: float) -> Optional[str]:
        """Update game modes menu logic."""
        # Handle input
        for event in self._pygame_adapter.get_events():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()

            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_UP, pygame.K_w):
                    self._selected_index = (self._selected_index - 1) % len(
                        self._menu_items
                    )
                elif event.key in (pygame.K_DOWN, pygame.K_s):
                    self._selected_index = (self._selected_index + 1) % len(
                        self._menu_items
                    )
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    # check if "Back to Menu" is selected (now at index 0)
                    if self._selected_index == 0:
                        # go back to main menu without changing mode
                        return "menu"

                    # save the selected game mode (adjust index by -1 since Back to Menu is first)
                    set_selected_game_mode(self._selected_index - 1)

                    # Get the resolved mode name and set on settings for restriction tracking
                    resolved_mode = get_resolved_game_mode()
                    self._settings.set_game_mode(resolved_mode)

                    # if Classic Snake Game is selected, reset settings to default
                    if (
                        self._selected_index == 1
                    ):  # Classic mode intentionally resets custom tweaks
                        self._settings.reset_to_defaults()
                        self._settings.save_settings()

                    elif self._selected_index == 2:  # Random
                        self._settings.reset_to_defaults()
                        self._settings.save_settings()

                    elif self._selected_index == 3:  # Head-Tail Swap mode
                        self._settings.reset_to_defaults()
                        self._settings.save_settings()

                    # go back to main menu
                    return "menu"
                elif event.key == pygame.K_ESCAPE:
                    # go back to main menu
                    return "menu"

            elif event.type == pygame.MOUSEMOTION:
                # handle mouse hover - only change cursor, not selection
                mouse_pos = event.pos
                # reset cursor to arrow by default
                pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)
                # check hover over each mode item to change cursor
                for i, item in enumerate(self._menu_items):
                    rect = self._get_mode_item_rect(i)
                    if rect and rect.collidepoint(mouse_pos):
                        pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)
                        break

            elif event.type == pygame.MOUSEWHEEL:
                # handle mouse wheel scroll
                if event.y > 0:
                    # scroll up - move selection up
                    self._selected_index = (self._selected_index - 1) % len(
                        self._menu_items
                    )
                elif event.y < 0:
                    # scroll down - move selection down
                    self._selected_index = (self._selected_index + 1) % len(
                        self._menu_items
                    )

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # handle left mouse click
                mouse_pos = event.pos
                for i, item in enumerate(self._menu_items):
                    rect = self._get_mode_item_rect(i)
                    if rect and rect.collidepoint(mouse_pos):
                        # check if "Back to Menu" is selected (now at index 0)
                        if i == 0:
                            # go back to main menu without changing mode
                            return "menu"

                        # same logic as RETURN key
                        set_selected_game_mode(i - 1)
                        resolved_mode = get_resolved_game_mode()
                        self._settings.set_game_mode(resolved_mode)

                        if i == 1:  # Classic mode
                            self._settings.reset_to_defaults()
                            self._settings.save_settings()
                        elif i == 2:  # Random
                            self._settings.reset_to_defaults()
                            self._settings.save_settings()
                        elif i == 3:  # Head-Tail Swap mode
                            self._settings.reset_to_defaults()
                            self._settings.save_settings()

                        return "menu"

        return None

    def render(self) -> None:
        """Render the game modes menu with proper spacing like settings."""
        # Clear screen
        self._renderer.fill(ARENA_PRIMARY_COLOR)

        # Draw title
        title = self._assets.render_custom(
            "Game Modes", MESSAGE_COLOR, int(self._width / 12)
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
                # Special color for "Back to Menu" button (blue)
                if i == 0:  # Back to Menu is now first
                    color = SCORE_COLOR if i == self._selected_index else (100, 100, 200)
                else:
                    color = SCORE_COLOR if i == self._selected_index else MESSAGE_COLOR

                # add arrow indicator if this mode is selected (confirmed)
                # Skip indicator for "Back to Menu" button
                display_text = item
                if i > 0 and (i - 1) == get_selected_game_mode():
                    display_text = f">> {item} <<"

                # Use consistent font size, centered
                text = self._assets.render_custom(
                    display_text, color, int(self._width / 25)
                )
                rect = text.get_rect(center=(self._width / 2, current_y))
                self._renderer.blit(text, rect)

                # Draw description for currently navigated mode (centered, wrapped)
                # Skip description for "Back to Menu" button
                if i == self._selected_index and i > 0:
                    description = self._get_description_for_index(i - 1)
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
            "Press ESC to go back", MESSAGE_COLOR, int(self._width / 50)
        )
        hint_rect = hint_text.get_rect(center=(self._width / 2, self._height * 0.95))
        self._renderer.blit(hint_text, hint_rect)

    def on_enter(self) -> None:
        """Called when entering game modes menu."""
        # start with cursor on currently selected game mode (+1 because Back to Menu is first)
        self._selected_index = get_selected_game_mode() + 1

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

    def _get_mode_item_rect(self, index: int) -> Optional[pygame.Rect]:
        """Calculate bounding box for mode item at given index.

        Args:
            index: Index of the mode item

        Returns:
            pygame.Rect representing the clickable area, or None if not visible
        """
        # calculate same layout as render() method
        row_h = int(self._height * 0.10)
        padding_y = int(self._height * 0.25)
        content_start_y = padding_y
        content_end_y = int(self._height * 0.88)

        # calculate scroll offset
        total_items_height = len(self._menu_items) * row_h
        available_height = content_end_y - padding_y

        if total_items_height > available_height:
            scroll_offset = max(0, (self._selected_index - 2) * row_h)
        else:
            scroll_offset = 0

        current_y = padding_y - scroll_offset + index * row_h

        # only return rect if item is in visible range
        if not (content_start_y <= current_y <= content_end_y):
            return None

        # render text to get exact size (same as render method)
        item = self._menu_items[index]
        display_text = item
        if index > 0 and (index - 1) == get_selected_game_mode():
            display_text = f">> {item} <<"

        text_surface = self._assets.render_custom(
            display_text, (255, 255, 255), int(self._width / 25)
        )
        text_rect = text_surface.get_rect(center=(self._width / 2, current_y))

        # add padding for larger clickable area
        padding = 20
        return text_rect.inflate(padding * 2, padding * 2)

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
