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

"""Menu scene."""

from __future__ import annotations

import pygame
from typing import Optional

from src.game.scenes.base_scene import BaseScene
from src.game.services.assets import GameAssets
from src.game.settings import GameSettings
from src.game.constants import ARENA_COLOR, MESSAGE_COLOR, SCORE_COLOR, WINDOW_TITLE


class MenuScene(BaseScene):
    """Main menu scene."""

    def __init__(
        self,
        pygame_adapter,
        renderer,
        width: int,
        height: int,
        assets: GameAssets,
        settings: GameSettings,
    ):
        """Initialize the menu scene.

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
        self._menu_items = ["Start Game", "Settings", "Quit"]

    def update(self, dt_ms: float) -> Optional[str]:
        """Update menu logic.

        Args:
            dt_ms: Delta time in milliseconds

        Returns:
            Next scene name or None
        """
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
                    if self._menu_items[self._selected_index] == "Start Game":
                        return "gameplay"
                    elif self._menu_items[self._selected_index] == "Settings":
                        return "settings"
                    elif self._menu_items[self._selected_index] == "Quit":
                        pygame.quit()
                        exit()
                elif event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    exit()

        return None

    def render(self) -> None:
        """Render the menu."""
        # Clear screen
        self._renderer.fill(ARENA_COLOR)

        # Get actual window dimensions
        window_width = self._renderer.width
        window_height = self._renderer.height

        # Draw title
        title = self._assets.render_custom(
            WINDOW_TITLE, MESSAGE_COLOR, int(window_width / 12)
        )
        title_rect = title.get_rect(center=(window_width / 2, window_height / 4))
        self._renderer.blit(title, title_rect)

        # Draw menu items
        for i, item in enumerate(self._menu_items):
            color = SCORE_COLOR if i == self._selected_index else MESSAGE_COLOR
            text = self._assets.render_small(item, color)
            rect = text.get_rect(
                center=(
                    window_width / 2,
                    window_height / 2 + i * (window_height * 0.12),
                )
            )
            self._renderer.blit(text, rect)

    def on_enter(self) -> None:
        """Called when entering menu."""
        self._selected_index = 0

        # Ensure background music is playing when entering menu
        # (it might have stopped if coming from game over)
        if self._settings.get("background_music"):
            GameAssets.play_background_music(loop=True)
