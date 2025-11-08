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
        self._selected_index = 0

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
                "description": "Deadly poisoned apples appear (Coming Soon)",
                "type": GameModeType.POISONED_APPLE,
                "available": False,
            },
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
                        self._game_modes
                    )
                elif event.key in (pygame.K_DOWN, pygame.K_s):
                    self._selected_index = (self._selected_index + 1) % len(
                        self._game_modes
                    )
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    selected_mode = self._game_modes[self._selected_index]
                    if selected_mode["available"]:
                        # save selected mode
                        self._selected_mode = selected_mode["type"]
                        # store selection for gameplay scene to read
                        self._store_game_mode_selection()
                        return "gameplay"
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

        # draw game modes
        start_y = self._height / 3
        spacing = self._height * 0.15

        for i, mode in enumerate(self._game_modes):
            # determine color based on availability and selection
            if i == self._selected_index:
                color = SCORE_COLOR if mode["available"] else GRID_COLOR
            else:
                color = MESSAGE_COLOR if mode["available"] else GRID_COLOR

            # render mode name
            mode_text = self._assets.render_small(mode["name"], color)
            mode_rect = mode_text.get_rect(
                center=(self._width / 2, start_y + i * spacing)
            )
            self._renderer.blit(mode_text, mode_rect)

            # render mode description (smaller text)
            desc_text = self._assets.render_custom(
                mode["description"], color, int(self._width / 50)
            )
            desc_rect = desc_text.get_rect(
                center=(self._width / 2, start_y + i * spacing + self._height * 0.04)
            )
            self._renderer.blit(desc_text, desc_rect)

        # draw hint footer
        hint_text = "[W/S] navigate   [Enter] select   [Esc] back to menu"
        hint = self._assets.render_custom(hint_text, GRID_COLOR, int(self._width / 50))
        hint_rect = hint.get_rect(center=(self._width / 2, self._height * 0.92))
        self._renderer.blit(hint, hint_rect)

    def on_enter(self) -> None:
        """Called when entering game modes scene."""
        self._selected_index = 0

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
