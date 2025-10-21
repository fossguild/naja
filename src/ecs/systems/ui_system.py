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

"""UISystem - handles all user interaction flows and menu navigation."""

import pygame
from enum import Enum
from src.ecs.systems.base_system import BaseSystem
from src.ecs.world import World
from src.core.rendering.pygame_surface_renderer import RenderEnqueue
from src.ecs.systems.assets import AssetsSystem


class StartDecision(Enum):
    """Decision returned by start menu."""

    START_GAME = "start_game"
    OPEN_SETTINGS = "open_settings"
    QUIT = "quit"


class SettingsResult:
    """Result returned by settings menu."""

    def __init__(self, needs_reset: bool = False, canceled: bool = False):
        self.needs_reset = needs_reset
        self.canceled = canceled


class ResetDecision(Enum):
    """Decision returned by reset warning dialog."""

    RESET = "reset"
    CANCEL = "cancel"


class GameOverDecision(Enum):
    """Decision returned by game over prompt."""

    RESTART = "restart"
    QUIT = "quit"


class UISystem(BaseSystem):
    """System responsible for UI state management and menu logic.

    This system manages UI state and logic, but does NOT handle input directly.
    Input is handled by InputSystem, which calls appropriate callbacks on this system.

    Responsibilities:
    - Menu state management (selected items, menu flow state)
    - UI logic and decision making
    - Delegating rendering to RenderSystem
    - Providing callback methods for InputSystem to call

    Note: This system receives commands via callbacks from InputSystem.
    It never processes pygame events directly.
    """

    def __init__(self, renderer: RenderEnqueue, assets: AssetsSystem):
        """Initialize the UISystem.

        Args:
            renderer: RenderEnqueue view to queue draw commands (enqueue-only access)
            assets: AssetsSystem instance for accessing fonts and sprites
        """
        self._renderer = renderer
        self._assets = assets

        # Menu state
        self._selected_index = 0
        self._menu_items = ["Start Game", "Settings"]
        self._setting_snapshots = {}
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
        """Start the menu loop and activate menu state.

        This method activates the menu state. The actual decision will be
        available via the get_pending_decision() method once a user makes a choice.
        """
        # Reset to first item when starting menu
        self._selected_index = 0
        self._menu_active = True
        self._pending_decision = None

        # Render initial menu state
        self._render_menu_frame()

    def is_menu_active(self) -> bool:
        """Check if menu is currently active.

        Returns:
            bool: True if menu is active and waiting for user input
        """
        return self._menu_active

    def get_pending_decision(self) -> StartDecision | None:
        """Get the pending decision if one has been made.

        Returns:
            StartDecision | None: The decision made by user, or None if still waiting
        """
        return self._pending_decision

    def _render_menu_frame(self) -> None:
        """Render the current menu frame."""
        # Clear screen
        self._renderer.fill((32, 32, 32))

        # Delegate rendering to renderer
        self._renderer.draw_start_menu(self._menu_items, self._selected_index)

    # Callback methods for InputSystem to call

    def handle_menu_up(self) -> None:
        """Handle UP key in menu (called by InputSystem)."""
        if self._menu_active:
            self._selected_index = (self._selected_index - 1) % len(self._menu_items)

    def handle_menu_down(self) -> None:
        """Handle DOWN key in menu (called by InputSystem)."""
        if self._menu_active:
            self._selected_index = (self._selected_index + 1) % len(self._menu_items)

    def handle_menu_select(self) -> None:
        """Handle ENTER/SPACE key in menu (called by InputSystem)."""
        if self._menu_active:
            selected_item = self._menu_items[self._selected_index]
            if selected_item == "Start Game":
                self._pending_decision = StartDecision.START_GAME
                self._menu_active = False
            elif selected_item == "Settings":
                self._pending_decision = StartDecision.OPEN_SETTINGS
                self._menu_active = False

    def handle_menu_quit(self) -> None:
        """Handle ESCAPE key in menu (called by InputSystem)."""
        if self._menu_active:
            self._pending_decision = StartDecision.QUIT
            self._menu_active = False

    def handle_app_quit(self) -> None:
        """Handle app quit (called by InputSystem)."""
        self._pending_decision = StartDecision.QUIT
        self._menu_active = False

    def run_settings_menu(self, io_adapter, settings) -> SettingsResult:
        """Run the settings menu loop until user confirms or cancels.

        Args:
            io_adapter: PygameIOAdapter instance for event handling and display updates
            settings: GameSettings instance to modify

        Returns:
            SettingsResult: Contains needs_reset and canceled flags
        """
        selected_index = 0

        # Snapshot original values of critical settings that need reset
        critical_settings = [
            "cells_per_side",
            "obstacle_difficulty",
            "initial_speed",
            "number_of_apples",
            "electric_walls",
        ]
        original_values = {key: settings.get(key) for key in critical_settings}

        # Event loop
        while True:
            # Get current settings values as dict for renderer
            settings_values = {
                field["key"]: settings.get(field["key"])
                for field in settings.MENU_FIELDS
            }

            # Render settings menu using renderer's built-in method
            self._renderer.draw_settings_menu(
                settings.MENU_FIELDS, selected_index, settings_values
            )
            io_adapter.update_display()

            # Process events
            for event in io_adapter.get_events():
                if event.type == pygame.QUIT:
                    # User closed window - revert changes
                    for key, value in original_values.items():
                        settings.set(key, value)
                    return SettingsResult(needs_reset=False, canceled=True)

                if event.type == pygame.KEYDOWN:
                    key = event.key

                    # Exit menu (save changes)
                    if key in (pygame.K_ESCAPE, pygame.K_RETURN):
                        # Check if critical settings changed
                        needs_reset = any(
                            settings.get(k) != original_values[k]
                            for k in critical_settings
                        )
                        return SettingsResult(needs_reset=needs_reset, canceled=False)

                    # Navigate down
                    elif key in (pygame.K_DOWN, pygame.K_s):
                        selected_index = (selected_index + 1) % len(
                            settings.MENU_FIELDS
                        )

                    # Navigate up
                    elif key in (pygame.K_UP, pygame.K_w):
                        selected_index = (selected_index - 1) % len(
                            settings.MENU_FIELDS
                        )

                    # Decrease value
                    elif key in (pygame.K_LEFT, pygame.K_a):
                        settings.step_setting(settings.MENU_FIELDS[selected_index], -1)

                    # Increase value
                    elif key in (pygame.K_RIGHT, pygame.K_d):
                        settings.step_setting(settings.MENU_FIELDS[selected_index], +1)

                    # Random colors (special key)
                    elif key == pygame.K_c:
                        settings.randomize_colors()

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

    # Additional callback methods for InputSystem

    def handle_pause(self) -> None:
        """Handle pause toggle (called by InputSystem)."""
        # TODO: Implement pause logic
        ...

    def handle_quit(self) -> None:
        """Handle quit request (called by InputSystem)."""
        self._pending_decision = StartDecision.QUIT
        self._menu_active = False

    def handle_open_settings(self) -> None:
        """Handle open settings request (called by InputSystem)."""
        # TODO: Implement settings menu
        ...

    def apply_settings(self, reset_objects: bool = False) -> None:
        """Apply pending settings changes.

        Args:
            reset_objects: Whether to recreate game objects
        """
        # TODO: Implement settings application
        # This should handle window resize, font reload, object recreation
        ...

    def needs_reset(self) -> bool:
        """Check if current settings changes require game reset.

        Returns:
            bool: True if reset is needed
        """
        # TODO: Implement reset detection logic
        return False

    def update(self, world: World) -> None:
        """Update method required by BaseSystem.

        Renders the current UI state when menu is active.

        Args:
            world: Game world (unused for UI system)
        """
        if self._menu_active:
            self._render_menu_frame()
