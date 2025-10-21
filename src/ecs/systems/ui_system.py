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

    def run_settings_menu(self) -> SettingsResult:
        """Run the settings menu loop until user confirms or cancels.

        Returns:
            SettingsResult: Contains needs_reset and canceled flags
        """
        # Settings menu fields (from old code)
        settings_fields = [
            {
                "key": "cells_per_side",
                "label": "Cells per side (needs reset)",
                "type": "int",
                "min": 10,
                "max": 60,
                "step": 1,
            },
            {
                "key": "initial_speed",
                "label": "Initial speed (needs reset)",
                "type": "float",
                "min": 1.0,
                "max": 40.0,
                "step": 0.5,
            },
            {
                "key": "max_speed",
                "label": "Max speed",
                "type": "float",
                "min": 4.0,
                "max": 60.0,
                "step": 1.0,
            },
            {"key": "death_sound", "label": "Death Sound", "type": "bool"},
            {
                "key": "obstacle_difficulty",
                "label": "Obstacles (needs reset)",
                "type": "select",
                "options": ["None", "Easy", "Medium", "Hard", "Impossible"],
            },
            {
                "key": "number_of_apples",
                "label": "Apples (needs reset)",
                "type": "int",
                "min": 1,
                "max": 30,
                "step": 1,
            },
            {"key": "background_music", "label": "Background Music", "type": "bool"},
            {
                "key": "reset_game_on_apply",
                "label": "Reset Game on Apply",
                "type": "bool",
            },
            {"key": "eat_sound", "label": "Eat sound", "type": "bool"},
            {
                "key": "electric_walls",
                "label": "Electric walls (needs reset)",
                "type": "bool",
            },
        ]

        # Default settings values (from old code)
        default_settings = {
            "cells_per_side": 16,
            "initial_speed": 4.0,
            "max_speed": 20.0,
            "death_sound": True,
            "obstacle_difficulty": "None",
            "number_of_apples": 1,
            "background_music": True,
            "reset_game_on_apply": False,
            "eat_sound": True,
            "electric_walls": True,
        }

        # Store current settings as snapshot for comparison
        self._setting_snapshots = default_settings.copy()
        current_settings = default_settings.copy()

        selected_index = 0
        settings_active = True

        while settings_active:
            # Render settings menu
            self._renderer.fill((32, 32, 32))
            self._renderer.draw_settings_menu(
                settings_fields, selected_index, current_settings
            )

            # Wait for input (this would be handled by MenuInputSystem in real implementation)
            # For now, return a placeholder result
            return SettingsResult(needs_reset=False, canceled=True)

    def prompt_reset_warning(self) -> ResetDecision:
        """Show dialog warning about game reset.

        Returns:
            ResetDecision: User's choice (RESET or CANCEL)
        """
        selected_option = 0  # 0 = Reset, 1 = Cancel
        dialog_active = True

        while dialog_active:
            # Render reset warning dialog
            self._renderer.fill((32, 32, 32))
            self._renderer.draw_reset_warning_dialog(selected_option)

            # Wait for input (this would be handled by MenuInputSystem in real implementation)
            # For now, return a placeholder result
            return ResetDecision.CANCEL

    def prompt_game_over(self, final_score: int) -> GameOverDecision:
        """Show game over screen with final score.

        Args:
            final_score: Final score to display

        Returns:
            GameOverDecision: User's choice (RESTART or QUIT)
        """
        selected_option = 0  # 0 = Restart, 1 = Quit
        dialog_active = True

        while dialog_active:
            # Render game over screen
            self._renderer.fill((32, 32, 32))
            self._renderer.draw_game_over_screen(final_score, selected_option)

            # Wait for input (this would be handled by MenuInputSystem in real implementation)
            # For now, return a placeholder result
            return GameOverDecision.RESTART

    # Additional callback methods for InputSystem

    def handle_pause(self) -> None:
        """Handle pause toggle (called by InputSystem)."""
        # TODO: Implement pause logic
        pass

    def handle_quit(self) -> None:
        """Handle quit request (called by InputSystem)."""
        self._pending_decision = StartDecision.QUIT
        self._menu_active = False

    def handle_open_settings(self) -> None:
        """Handle open settings request (called by InputSystem)."""
        # TODO: Implement settings menu
        pass

    def apply_settings(self, reset_objects: bool = False) -> None:
        """Apply pending settings changes.

        Args:
            reset_objects: Whether to recreate game objects
        """
        # TODO: Implement settings application
        # This should handle window resize, font reload, object recreation
        pass

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
