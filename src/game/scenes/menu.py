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

from game.scenes.base_scene import BaseScene
from game.services.assets import GameAssets
from game.settings import GameSettings
from game.constants import ARENA_PRIMARY_COLOR, MESSAGE_COLOR, SCORE_COLOR, WINDOW_TITLE


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
        self._menu_items = ["Start Game", "Game Modes", "Settings", "Quit"]

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
                    elif self._menu_items[self._selected_index] == "Game Modes":
                        return "game_modes"
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
        self._renderer.fill(ARENA_PRIMARY_COLOR)

        # Draw title (bigger and more prominent)
        title = self._assets.render_custom(
            WINDOW_TITLE, MESSAGE_COLOR, int(self._width / 8)
        )
        title_rect = title.get_rect(center=(self._width / 2, self._height / 5))
        self._renderer.blit(title, title_rect)

        # Draw selected game mode below title
        mode_text = self._get_selected_mode_text()
        mode_surface = self._assets.render_custom(
            mode_text, (150, 150, 150), int(self._width / 32)
        )
        mode_rect = mode_surface.get_rect(
            center=(self._width / 2, self._height / 5 + self._height * 0.10)
        )
        self._renderer.blit(mode_surface, mode_rect)

        # Draw menu items
        for i, item in enumerate(self._menu_items):
            color = SCORE_COLOR if i == self._selected_index else MESSAGE_COLOR
            text = self._assets.render_small(item, color)
            rect = text.get_rect(
                center=(self._width / 2, self._height / 2 + i * (self._height * 0.12))
            )
            self._renderer.blit(text, rect)

    def on_enter(self) -> None:
        """Called when entering menu."""
        self._selected_index = 0

        # play menu music when entering menu
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

    def _get_selected_mode_text(self) -> str:
        """Get text for currently selected game mode.

        Returns:
            Display text for selected game mode
        """
        try:
            from game.scenes.game_modes import get_display_mode_name

            return get_display_mode_name()
        except Exception:
            return "Classic Snake Game"
