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

"""Game modes selection scene."""

from __future__ import annotations

import pygame
from typing import Optional

from src.game.scenes.base_scene import BaseScene
from src.game.services.assets import GameAssets
from src.game.settings import GameSettings
from src.game.constants import ARENA_COLOR, MESSAGE_COLOR, SCORE_COLOR, GRID_COLOR
from src.ecs.components.game_mode import GameModeType


class GameModesScene(BaseScene):
    """Game modes selection scene."""

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
        self._selected_index = 0  # for navigation
        self._confirmed_mode_index = 0  # which mode is actually selected

        # define available game modes
        self._game_modes = [
            {
                "name": "Classic Mode",
                "description": "Traditional snake game with apples",
                "type": GameModeType.CLASSIC,
                "available": True,
            },
            {
                "name": "More Fruits Mode",
                "description": "Multiple fruit varieties with different effects",
                "type": GameModeType.MORE_FRUITS,
                "available": True,
            },
            {
                "name": "Poisoned Apple Mode",
                "description": "Deadly dark purple apples that end the game instantly",
                "type": GameModeType.POISONED_APPLE,
                "available": True,
            },
        ]

        # add "Start Game" menu item
        self._menu_items = self._game_modes + [
            {
                "name": "Start Game",
                "description": "Begin playing with selected mode",
                "type": None,
                "available": True,
            }
        ]

        self._selected_mode = GameModeType.CLASSIC

    def update(self, dt_ms: float) -> Optional[str]:
        """Update game modes selection logic.

        Args:
            dt_ms: Delta time in milliseconds

        Returns:
            Next scene name or None
        """
        # handle input
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
                    selected_item = self._menu_items[self._selected_index]

                    if selected_item["name"] == "Start Game":
                        # start game with confirmed mode
                        confirmed_mode = self._game_modes[self._confirmed_mode_index]
                        self._selected_mode = confirmed_mode["type"]
                        self._store_game_mode_selection()
                        return "gameplay"
                    elif selected_item["available"]:
                        # select this mode (but don't start yet)
                        self._confirmed_mode_index = self._selected_index
                elif event.key == pygame.K_ESCAPE:
                    # return to main menu
                    return "menu"

        return None

    def render(self) -> None:
        """Render the game modes selection menu."""
        # clear screen
        self._renderer.fill(ARENA_COLOR)

        # draw title
        title = self._assets.render_custom(
            "Game Modes", MESSAGE_COLOR, int(self._width / 12)
        )
        title_rect = title.get_rect(center=(self._width / 2, self._height / 8))
        self._renderer.blit(title, title_rect)

        # draw game modes and start button
        start_y = self._height / 3.5
        spacing = self._height * 0.13

        for i, item in enumerate(self._menu_items):
            is_start_button = item["name"] == "Start Game"
            is_game_mode = not is_start_button

            # calculate position (add extra spacing before Start Game button)
            y_pos = start_y + i * spacing
            if is_start_button:
                y_pos += spacing * 0.4  # extra gap before start button

            # determine color based on state
            if i == self._selected_index:
                # currently navigating here
                color = SCORE_COLOR if item["available"] else GRID_COLOR
            elif is_game_mode and i == self._confirmed_mode_index:
                # this mode is confirmed/selected (green)
                color = (100, 255, 100)
            else:
                # normal state
                color = MESSAGE_COLOR if item["available"] else GRID_COLOR

            # add visual indicator for confirmed mode
            prefix = "► " if (is_game_mode and i == self._confirmed_mode_index) else ""
            display_name = prefix + item["name"]

            # render item name
            item_text = self._assets.render_small(display_name, color)
            item_rect = item_text.get_rect(center=(self._width / 2, y_pos))
            self._renderer.blit(item_text, item_rect)

            # render item description (smaller text, only for non-start-button items)
            if item["description"]:
                desc_text = self._assets.render_custom(
                    item["description"], color, int(self._width / 55)
                )
                desc_rect = desc_text.get_rect(
                    center=(self._width / 2, y_pos + self._height * 0.035)
                )
                self._renderer.blit(desc_text, desc_rect)

        # draw hint footer
        hint_text = "[W/S] navigate   [Enter] select/start   [Esc] back"
        hint = self._assets.render_custom(hint_text, GRID_COLOR, int(self._width / 50))
        hint_rect = hint.get_rect(center=(self._width / 2, self._height * 0.92))
        self._renderer.blit(hint, hint_rect)

    def on_enter(self) -> None:
        """Called when entering game modes scene."""
        self._selected_index = 0
        self._confirmed_mode_index = 0  # default to first mode (Classic)

    def get_selected_mode(self) -> GameModeType:
        """Get the currently selected game mode.

        Returns:
            Selected game mode type
        """
        return self._selected_mode

    def _store_game_mode_selection(self) -> None:
        """Store the selected game mode in a global settings variable.

        This is a temporary solution until we have proper scene communication.
        """
        # store in global variable for gameplay scene to read
        import src.game.scenes.game_modes as gm_module

        gm_module._SELECTED_GAME_MODE = self._selected_mode


# module-level variable for scene communication
_SELECTED_GAME_MODE = GameModeType.CLASSIC


def get_selected_game_mode() -> GameModeType:
    """Get the currently selected game mode.

    Returns:
        Selected game mode type
    """
    return _SELECTED_GAME_MODE
