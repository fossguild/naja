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
from game.constants import ARENA_COLOR, MESSAGE_COLOR, SCORE_COLOR

# global variable to store selected game mode
_selected_game_mode = 0  # 0 = Classic, 1 = Random

# Available actual game modes (not including random)
ACTUAL_GAME_MODES = [
    "Classic Snake Game",
    # Future modes will be added here:
    # "More Fruits",
    # "Poisoned Apple",
    # "Flying Apple",
    # etc.
]


def get_selected_game_mode() -> int:
    """Get the currently selected game mode.

    Returns:
        Index of selected game mode (0=Classic, 1=Random)
    """
    return _selected_game_mode


def set_selected_game_mode(mode: int) -> None:
    """Set the selected game mode.

    Args:
        mode: Index of game mode to select (0=Classic, 1=Random)
    """
    global _selected_game_mode
    _selected_game_mode = mode


def get_resolved_game_mode() -> str:
    """Get the actual game mode to play.

    If Random is selected, picks a random actual game mode.
    Otherwise returns the selected mode name.

    Returns:
        Name of the actual game mode to play
    """
    if _selected_game_mode == 1:  # Random mode
        return random.choice(ACTUAL_GAME_MODES)
    else:  # Classic or other direct modes
        return ACTUAL_GAME_MODES[0]  # For now, only Classic exists


def get_display_mode_name() -> str:
    """Get the display name for the selected mode.

    Returns:
        Display name showing what will be played
    """
    if _selected_game_mode == 0:
        return "Classic Snake Game"
    elif _selected_game_mode == 1:
        return "🎲 Random"
    else:
        return "Classic Snake Game"


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
        self._menu_items = ["Classic Snake Game", "🎲 Random"]

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
                    # go back to main menu
                    return "menu"
                elif event.key == pygame.K_ESCAPE:
                    # go back to main menu
                    return "menu"

        return None

    def render(self) -> None:
        """Render the game modes menu."""
        # Clear screen
        self._renderer.fill(ARENA_COLOR)

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
            if i == get_selected_game_mode():
                display_text = f">> {item} <<"

            text = self._assets.render_small(display_text, color)
            rect = text.get_rect(
                center=(self._width / 2, self._height / 2 + i * (self._height * 0.12))
            )
            self._renderer.blit(text, rect)

        # Draw description for selected mode
        if self._selected_index == 1:  # Random mode
            description = "Randomly selects a game mode"
            desc_text = self._assets.render_custom(
                description, (120, 120, 120), int(self._width / 45)
            )
            desc_rect = desc_text.get_rect(center=(self._width / 2, self._height * 0.7))
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
