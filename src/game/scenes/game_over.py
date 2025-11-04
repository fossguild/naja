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

"""Game over scene."""

from __future__ import annotations

import pygame
import sys
from typing import Optional

from src.game.scenes.base_scene import BaseScene
from src.game.services.assets import GameAssets
from src.game.constants import ARENA_COLOR


class GameOverScene(BaseScene):
    """Game over scene."""

    def __init__(
        self,
        pygame_adapter,
        renderer,
        width: int,
        height: int,
        assets: GameAssets,
        death_reason: str = "",
        settings=None,
    ):
        """Initialize the game over scene.

        Args:
            pygame_adapter: Pygame IO adapter
            renderer: Renderer for drawing
            width: Scene width
            height: Scene height
            assets: Game assets
            death_reason: Reason for game over
            settings: Optional GameSettings instance
        """
        super().__init__(pygame_adapter, renderer, width, height)
        self._assets = assets
        self._death_reason = death_reason
        self._settings = settings

    def update(self, dt_ms: float) -> Optional[str]:
        """Update game over logic.

        Args:
            dt_ms: Delta time in milliseconds

        Returns:
            Next scene name or None
        """
        # Handle input
        for event in self._pygame_adapter.get_events():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    return "gameplay"  # restart game directly
                elif event.key == pygame.K_q:
                    return "menu"  # return to main menu

        return None

    def render(self) -> None:
        """Render the game over screen."""
        # Clear screen with arena color
        self._renderer.fill(ARENA_COLOR)

        # Draw game over text
        try:
            # Get actual window dimensions
            window_width = self._renderer.width
            window_height = self._renderer.height

            # calculate font sizes based on window dimensions
            big_font_size = int(window_width / 8)
            small_font_size = int(window_width / 25)

            # create fonts with same font file and sizing
            font_path = "assets/font/GetVoIP-Grotesque.ttf"

            try:
                # try to load the font
                big_font = pygame.font.Font(font_path, big_font_size)
                small_font = pygame.font.Font(font_path, small_font_size)
            except Exception:
                # fallback to default font if GetVoIP font not found
                big_font = pygame.font.Font(None, big_font_size)
                small_font = pygame.font.Font(None, small_font_size)

            # MESSAGE_COLOR: gray
            message_color = (128, 128, 128)

            # "Game Over" text centered
            game_over_text = big_font.render("Game Over", True, message_color)
            game_over_rect = game_over_text.get_rect(
                center=(window_width // 2, window_height / 2.6)
            )

            # "Press Enter/Space to restart • Q to menu" text below
            restart_text = small_font.render(
                "Press Enter/Space to play again • Q to menu", True, message_color
            )
            restart_rect = restart_text.get_rect(
                center=(window_width // 2, window_height / 1.8)
            )

            # blit text to main surface
            self._renderer.blit(game_over_text, game_over_rect)
            self._renderer.blit(restart_text, restart_rect)

        except Exception:
            # if font loading fails, just show arena color
            pass

    def on_enter(self) -> None:
        """Called when entering game over."""
        # Play death song (like old code) - only if audio is not muted
        if not self._settings or self._settings.get("background_music"):
            try:
                pygame.mixer.music.load("assets/sound/death_song.mp3")
                pygame.mixer.music.play(-1)  # loop
            except Exception:
                pass

    def on_exit(self) -> None:
        """Called when exiting game over."""
        # Stop death song
        try:
            pygame.mixer.music.stop()
        except Exception:
            pass
