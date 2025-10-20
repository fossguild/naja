#!/usr/bin/env python3
#
#   Copyright (c) 2023, Monaco F. J. <monaco@usp.br>
#   Copyright (c) 2024, Gabriel R. <gabiruuu@example.com>
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

"""MenuInputSystem - handles input specifically for menu navigation."""

import pygame
from typing import Optional, Any
from src.ecs.systems.base_system import BaseSystem
from src.ecs.world import World


class MenuInputSystem(BaseSystem):
    """System for handling input specifically during menu navigation.

    This system processes pygame events and routes menu-specific input
    to UISystem callback methods. It's designed to work alongside
    the main InputSystem for different game states.

    Responsibilities:
    - Process pygame events for menu navigation
    - Route menu input to UISystem callbacks
    - Handle menu-specific keys (arrows, enter, escape)

    Note: This system only handles input routing. UI logic is handled
    by UISystem through callback methods.
    """

    def __init__(
        self,
        pygame_adapter: Optional[Any] = None,
        ui_system: Optional[Any] = None,
    ):
        """Initialize the MenuInputSystem.

        Args:
            pygame_adapter: Pygame IO adapter for reading events
            ui_system: UISystem instance to receive callback calls
        """
        self._pygame_adapter = pygame_adapter
        self._ui_system = ui_system

    def update(self, world: World) -> None:
        """Process input events and call appropriate UI callbacks.

        Args:
            world: ECS world containing entities and components
        """
        if not self._pygame_adapter or not self._ui_system:
            return

        # Get all pygame events
        events = self._pygame_adapter.get_events()

        # Process each event
        for event in events:
            if event.type == pygame.QUIT:
                self._ui_system.handle_app_quit()
            elif event.type == pygame.KEYDOWN:
                self._handle_keydown(event.key)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                self._handle_mouse_click(event)

    def _handle_keydown(self, key: int) -> None:
        """Handle key down events for menu navigation.

        Args:
            key: Pygame key constant
        """
        if key in (pygame.K_UP, pygame.K_w):
            self._ui_system.handle_menu_up()
        elif key in (pygame.K_DOWN, pygame.K_s):
            self._ui_system.handle_menu_down()
        elif key in (pygame.K_RETURN, pygame.K_SPACE):
            self._ui_system.handle_menu_select()
        elif key == pygame.K_ESCAPE:
            self._ui_system.handle_menu_quit()
        elif key == pygame.K_q:
            self._ui_system.handle_quit()
