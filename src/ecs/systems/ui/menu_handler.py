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

"""Start menu handler for main menu navigation."""

import pygame
from enum import Enum
from core.rendering.pygame_surface_renderer import RenderEnqueue
from ecs.systems.assets import AssetsSystem


class StartDecision(Enum):
    """Decision returned by start menu."""

    START_GAME = "start_game"
    OPEN_SETTINGS = "open_settings"
    QUIT = "quit"


class MenuHandler:
    """Handles start menu navigation and rendering.

    Responsibilities:
    - Menu state management (selected item)
    - Menu input processing
    - Delegating rendering to RenderSystem
    - Returning user decisions
    """

    def __init__(self, renderer: RenderEnqueue, assets: AssetsSystem):
        """Initialize the MenuHandler.

        Args:
            renderer: RenderEnqueue view to queue draw commands
            assets: AssetsSystem instance for accessing fonts and sprites
        """
        self._renderer = renderer
        self._assets = assets
        self._selected_index = 0
        self._menu_items = ["Start Game", "Settings"]
        self._menu_active = False
        self._pending_decision = None

    def run_start_menu(self, io_adapter) -> StartDecision:
        """Run the start menu loop until user makes a decision.

        This method runs the complete menu interaction cycle and returns
        the user's decision. It handles its own event loop internally.

        Args:
            io_adapter: PygameIOAdapter instance for event handling and display updates

        Returns:
            StartDecision: The decision made by the user (START_GAME, OPEN_SETTINGS, or QUIT)
        """
        # Start the menu loop
        self.start_menu_loop()

        # Event loop - wait for user decision
        while self._pending_decision is None:
            # Render current menu state
            self._render_menu_frame()
            io_adapter.update_display()

            # Process events
            for event in io_adapter.get_events():
                if event.type == pygame.QUIT:
                    self.handle_app_quit()
                    break

                if event.type == pygame.KEYDOWN:
                    key = event.key
                    if key in (pygame.K_UP, pygame.K_w):
                        self.handle_menu_up()
                    elif key in (pygame.K_DOWN, pygame.K_s):
                        self.handle_menu_down()
                    elif key in (pygame.K_RETURN, pygame.K_SPACE):
                        self.handle_menu_select()
                    elif key == pygame.K_ESCAPE:
                        self.handle_menu_quit()

        return self._pending_decision

    def start_menu_loop(self) -> None:
        """Start the menu loop and activate menu state."""
        # Reset to first item when starting menu
        self._selected_index = 0
        self._menu_active = True
        self._pending_decision = None

        # Render initial menu state
        self._render_menu_frame()

    def is_menu_active(self) -> bool:
        """Check if menu is currently active."""
        return self._menu_active

    def get_pending_decision(self) -> StartDecision | None:
        """Get the pending decision if one has been made."""
        return self._pending_decision

    def _render_menu_frame(self) -> None:
        """Render the current menu frame."""
        # Clear screen
        self._renderer.fill((32, 32, 32))

        # Delegate rendering to renderer
        self._renderer.draw_start_menu(self._menu_items, self._selected_index)

    # Callback methods for input handling

    def handle_menu_up(self) -> None:
        """Handle UP key in menu."""
        if self._menu_active:
            self._selected_index = (self._selected_index - 1) % len(self._menu_items)

    def handle_menu_down(self) -> None:
        """Handle DOWN key in menu."""
        if self._menu_active:
            self._selected_index = (self._selected_index + 1) % len(self._menu_items)

    def handle_menu_select(self) -> None:
        """Handle ENTER/SPACE key in menu."""
        if self._menu_active:
            selected_item = self._menu_items[self._selected_index]
            if selected_item == "Start Game":
                self._pending_decision = StartDecision.START_GAME
                self._menu_active = False
            elif selected_item == "Settings":
                self._pending_decision = StartDecision.OPEN_SETTINGS
                self._menu_active = False

    def handle_menu_quit(self) -> None:
        """Handle ESCAPE key in menu."""
        if self._menu_active:
            self._pending_decision = StartDecision.QUIT
            self._menu_active = False

    def handle_app_quit(self) -> None:
        """Handle app quit (window close)."""
        self._pending_decision = StartDecision.QUIT
        self._menu_active = False
