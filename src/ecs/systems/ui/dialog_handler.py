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

"""Dialog handler for reset warning and game over screens."""

import pygame
from enum import Enum
from src.core.rendering.pygame_surface_renderer import RenderEnqueue
from src.ecs.systems.assets import AssetsSystem


class ResetDecision(Enum):
    """Decision returned by reset warning dialog."""

    RESET = "reset"
    CANCEL = "cancel"


class GameOverDecision(Enum):
    """Decision returned by game over prompt."""

    RESTART = "restart"
    QUIT = "quit"


class DialogHandler:
    """Handles dialog screens (reset warning, game over).

    Responsibilities:
    - Dialog navigation and input
    - Delegating rendering to RenderSystem
    - Returning user decisions
    """

    def __init__(self, renderer: RenderEnqueue, assets: AssetsSystem):
        """Initialize the DialogHandler.

        Args:
            renderer: RenderEnqueue view to queue draw commands
            assets: AssetsSystem instance for accessing fonts and sprites
        """
        self._renderer = renderer
        self._assets = assets

    def prompt_reset_warning(self, io_adapter) -> ResetDecision:
        """Show dialog warning about game reset.

        Args:
            io_adapter: PygameIOAdapter instance for event handling and display updates

        Returns:
            ResetDecision: User's choice (RESET or CANCEL)
        """
        selected = 0

        # Event loop
        while True:
            # Render warning dialog using renderer's built-in method
            self._renderer.draw_reset_warning_dialog(selected)
            io_adapter.update_display()

            # Process events
            for event in io_adapter.get_events():
                if event.type == pygame.QUIT:
                    # User closed window - cancel changes
                    return ResetDecision.CANCEL

                if event.type == pygame.KEYDOWN:
                    key = event.key

                    # Navigate up
                    if key in (pygame.K_UP, pygame.K_w):
                        selected = (selected - 1) % 2  # 2 options

                    # Navigate down
                    elif key in (pygame.K_DOWN, pygame.K_s):
                        selected = (selected + 1) % 2  # 2 options

                    # Confirm selection
                    elif key in (pygame.K_RETURN, pygame.K_SPACE):
                        if selected == 0:  # Reset Now
                            return ResetDecision.RESET
                        else:  # Cancel Changes
                            return ResetDecision.CANCEL

                    # ESC always cancels
                    elif key == pygame.K_ESCAPE:
                        return ResetDecision.CANCEL

    def prompt_game_over(
        self, io_adapter, final_score: int, settings=None
    ) -> GameOverDecision:
        """Show game over screen with final score.

        Args:
            io_adapter: PygameIOAdapter instance for event handling and display updates
            final_score: Final score to display
            settings: Optional GameSettings instance for sound/music control

        Returns:
            GameOverDecision: User's choice (RESTART or QUIT)
        """
        # Play death sound effect if enabled
        if settings and settings.get("death_sound"):
            # Audio will be handled by AudioSystem in full ECS implementation
            pass

        # Switch to death music if enabled
        if settings and settings.get("background_music"):
            # Music will be handled by AudioSystem in full ECS implementation
            pass

        # No selection index for game over (just wait for key)
        selected_option = 0  # 0 = restart, 1 = quit

        # Event loop - wait for user decision
        while True:
            # Render game over screen using renderer's built-in method
            self._renderer.draw_game_over_screen(final_score, selected_option)
            io_adapter.update_display()

            # Process events
            for event in io_adapter.get_events():
                if event.type == pygame.QUIT:
                    if settings and settings.get("background_music"):
                        # Music will be handled by AudioSystem
                        pass
                    return GameOverDecision.QUIT

                if event.type == pygame.KEYDOWN:
                    key = event.key

                    # Restart game
                    if key in (pygame.K_RETURN, pygame.K_SPACE):
                        if settings and settings.get("background_music"):
                            # Music will be handled by AudioSystem
                            pass
                        return GameOverDecision.RESTART

                    # Quit game
                    elif key == pygame.K_q:
                        if settings and settings.get("background_music"):
                            # Music will be handled by AudioSystem
                            pass
                        return GameOverDecision.QUIT
