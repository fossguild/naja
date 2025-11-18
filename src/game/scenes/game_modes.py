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
        available = ", ".join(mode["name"] for mode in ACTUAL_GAME_MODES)
        return f"Random ({available})"
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
                    # save the selected game mode
                    set_selected_game_mode(self._selected_index)
                    # if Classic Snake Game is selected, reset settings to default
                    if (
                        self._selected_index == 0
                    ):  # Classic mode intentionally resets custom tweaks
                        self._settings.reset_to_defaults()
                        self._settings.save_settings()
                    # go back to main menu
                    return "menu"
                elif event.key == pygame.K_ESCAPE:
                    # go back to main menu
                    return "menu"

        return None

    def render(self) -> None:
        """Render the game modes menu."""
        # Clear screen
        self._renderer.fill(ARENA_PRIMARY_COLOR)

        # Draw title
        title = self._assets.render_custom(
            "Game Modes", MESSAGE_COLOR, int(self._width / 15)
        )
        title_rect = title.get_rect(center=(self._width / 2, self._height / 4))
        self._renderer.blit(title, title_rect)

        # Draw menu items
        for i, item in enumerate(self._menu_items):
            color = SCORE_COLOR if i == self._selected_index else MESSAGE_COLOR

            # add arrow indicator if this mode is selected (confirmed)
            display_text = item
            if i == self._selected_index:
                display_text = f">> {item} <<"

            text = self._assets.render_small(display_text, color)
            rect = text.get_rect(
                center=(self._width / 2, self._height / 2 + i * (self._height * 0.12))
            )
            self._renderer.blit(text, rect)

        # Draw description for selected mode
        description = self._get_description_for_index(self._selected_index)
        if description:
            desc_text = self._assets.render_custom(
                description, (120, 120, 120), int(self._width / 45)
            )
            desc_rect = desc_text.get_rect(
                center=(
                    self._width / 2,
                    self._height / 2
                    + self._selected_index * (self._height * 0.12)
                    + self._height * 0.08,
                )
            )
            self._renderer.blit(desc_text, desc_rect)

        # Draw back instruction
        back_text = self._assets.render_custom(
            "Press ESC to go back", MESSAGE_COLOR, int(self._width / 40)
        )
        back_rect = back_text.get_rect(
            center=(self._width / 2, self._height - self._height * 0.1)
        )
        self._renderer.blit(back_text, back_rect)

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
