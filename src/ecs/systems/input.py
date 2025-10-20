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

"""Input system for handling user input events.

This system converts raw pygame events into game actions by calling
registered callback functions.
"""

from typing import Optional, Callable, Any

import pygame

from src.ecs.systems.base_system import BaseSystem
from src.ecs.world import World


class InputSystem(BaseSystem):
    """System for handling user input from keyboard and mouse.

    Reads: pygame events (via pygame_adapter)
    Writes: None (delegates to callbacks)
    Emits: Commands via callbacks

    Responsibilities:
    - Convert keyboard input to direction changes
    - Handle game control keys (pause, quit, menu)
    - Handle settings shortcuts (music toggle, palette randomize)
    - Delegate actions to registered callbacks

    Note: This system acts as an input router, processing pygame events
    and calling appropriate callbacks. It does not directly modify game state.
    """

    def __init__(
        self,
        pygame_adapter: Optional[Any] = None,
        direction_callback: Optional[Callable[[int, int], None]] = None,
        get_current_direction_callback: Optional[Callable[[], tuple[int, int]]] = None,
        quit_callback: Optional[Callable[[], None]] = None,
        pause_callback: Optional[Callable[[], None]] = None,
        menu_callback: Optional[Callable[[], None]] = None,
        music_toggle_callback: Optional[Callable[[], None]] = None,
        palette_randomize_callback: Optional[Callable[[], None]] = None,
    ):
        """Initialize the InputSystem.

        Args:
            pygame_adapter: Pygame IO adapter for reading events
            direction_callback: Function to call with (dx, dy) for direction changes
            get_current_direction_callback: Function to get current (dx, dy) direction
            quit_callback: Function to call when quit is requested
            pause_callback: Function to call when pause is requested
            menu_callback: Function to call when menu is requested
            music_toggle_callback: Function to call when music toggle is requested
            palette_randomize_callback: Function to call when palette randomize is requested
        """
        self._pygame_adapter = pygame_adapter
        self._direction_callback = direction_callback
        self._get_current_direction_callback = get_current_direction_callback
        self._quit_callback = quit_callback
        self._pause_callback = pause_callback
        self._menu_callback = menu_callback
        self._music_toggle_callback = music_toggle_callback
        self._palette_randomize_callback = palette_randomize_callback

    def update(self, world: World) -> None:
        """Process input events and call appropriate callbacks.

        Args:
            world: ECS world containing entities and components
        """
        if not self._pygame_adapter:
            return

        # get all pygame events
        events = self._pygame_adapter.get_events()

        # process each event
        for event in events:
            if event.type == pygame.QUIT:
                self._handle_quit()
            elif event.type == pygame.KEYDOWN:
                self._handle_keydown(event.key)

    def _handle_quit(self) -> None:
        """Handle quit event (window close button)."""
        if self._quit_callback:
            self._quit_callback()

    def _handle_keydown(self, key: int) -> None:
        """Handle key down events.

        Args:
            key: Pygame key constant
        """
        # movement keys - call direction callback with 180° turn prevention
        current_dx, current_dy = self._get_current_direction()

        if key in (pygame.K_DOWN, pygame.K_s):
            self._set_direction(0, 1, current_dx, current_dy)
        elif key in (pygame.K_UP, pygame.K_w):
            self._set_direction(0, -1, current_dx, current_dy)
        elif key in (pygame.K_RIGHT, pygame.K_d):
            self._set_direction(1, 0, current_dx, current_dy)
        elif key in (pygame.K_LEFT, pygame.K_a):
            self._set_direction(-1, 0, current_dx, current_dy)
        # control keys
        elif key == pygame.K_q:
            self._handle_quit()
        elif key == pygame.K_p:
            self._handle_pause()
        elif key in (pygame.K_m, pygame.K_ESCAPE):
            self._handle_menu()
        elif key == pygame.K_n:
            self._handle_music_toggle()
        elif key == pygame.K_c:
            self._handle_palette_randomize()

    def _set_direction(
        self, dx: int, dy: int, current_dx: int = 0, current_dy: int = 0
    ) -> None:
        """Call direction callback with new direction if valid.

        Args:
            dx: X direction (-1, 0, 1)
            dy: Y direction (-1, 0, 1)
            current_dx: Current X direction (to prevent 180° turns)
            current_dy: Current Y direction (to prevent 180° turns)
        """
        # prevent 180-degree turns (same logic as old code)
        if dx != 0 and current_dx != -dx:  # horizontal movement
            if self._direction_callback:
                self._direction_callback(dx, dy)
        elif dy != 0 and current_dy != -dy:  # vertical movement
            if self._direction_callback:
                self._direction_callback(dx, dy)

    def _get_current_direction(self) -> tuple[int, int]:
        """Get current direction from callback or return (0, 0).

        Returns:
            tuple: (current_dx, current_dy) or (0, 0) if no callback
        """
        if self._get_current_direction_callback:
            return self._get_current_direction_callback()
        return (0, 0)

    def _handle_pause(self) -> None:
        """Handle pause key press."""
        if self._pause_callback:
            self._pause_callback()

    def _handle_menu(self) -> None:
        """Handle menu key press."""
        if self._menu_callback:
            self._menu_callback()

    def _handle_music_toggle(self) -> None:
        """Handle music toggle key press."""
        if self._music_toggle_callback:
            self._music_toggle_callback()

    def _handle_palette_randomize(self) -> None:
        """Handle palette randomize key press."""
        if self._palette_randomize_callback:
            self._palette_randomize_callback()
