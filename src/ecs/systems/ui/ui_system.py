#!/usr/bin/env python3
#
#   Copyright (c) 2023, Monaco F. J. <monaco@usp.br>
#   Copyright (c) 2024, Felipe Diniz <lfelipediniz@usp.br>
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

"""UISystem - orchestrator for all UI subsystems.

This is a lightweight orchestrator that delegates to specialized handlers:
- MenuHandler: Start menu
- SettingsHandler: Settings menu
- DialogHandler: Reset warning and game over dialogs
- CommandConverter: Event-to-command translation
"""

from typing import Optional, Callable, Tuple
import pygame

from src.ecs.systems.base_system import BaseSystem
from src.ecs.world import World
from src.core.rendering.pygame_surface_renderer import RenderEnqueue
from src.ecs.systems.assets import AssetsSystem
from src.ecs.components.commands import Command

from .menu_handler import MenuHandler, StartDecision
from .settings_handler import SettingsHandler, SettingsResult
from .dialog_handler import DialogHandler, ResetDecision, GameOverDecision
from .command_converter import CommandConverter


class UISystem(BaseSystem):
    """System responsible for UI orchestration.

    This system coordinates UI flows but delegates implementation to specialized handlers.
    It maintains backward compatibility with the existing interface while providing
    a cleaner internal structure.

    Responsibilities:
    - Orchestrating UI handlers
    - Providing unified interface for UI operations
    - Managing handler lifecycle
    """

    def __init__(
        self,
        renderer: RenderEnqueue,
        assets: AssetsSystem,
        get_current_direction: Optional[Callable[[], Tuple[int, int]]] = None,
    ):
        """Initialize the UISystem.

        Args:
            renderer: RenderEnqueue view to queue draw commands (enqueue-only access)
            assets: AssetsSystem instance for accessing fonts and sprites
            get_current_direction: Optional callback to get current snake direction (dx, dy)
        """
        self._renderer = renderer
        self._assets = assets

        # Initialize specialized handlers
        self._menu_handler = MenuHandler(renderer, assets)
        self._settings_handler = SettingsHandler(renderer, assets)
        self._dialog_handler = DialogHandler(renderer, assets)
        self._command_converter = CommandConverter(get_current_direction)

    # Compatibility properties for backward compatibility with tests
    # These delegate to the internal MenuHandler

    @property
    def _selected_index(self):
        """Get selected index from menu handler (for backward compatibility)."""
        return self._menu_handler._selected_index

    @_selected_index.setter
    def _selected_index(self, value):
        """Set selected index in menu handler (for backward compatibility)."""
        self._menu_handler._selected_index = value

    @property
    def _menu_active(self):
        """Get menu active state from menu handler (for backward compatibility)."""
        return self._menu_handler._menu_active

    @_menu_active.setter
    def _menu_active(self, value):
        """Set menu active state in menu handler (for backward compatibility)."""
        self._menu_handler._menu_active = value

    @property
    def _pending_decision(self):
        """Get pending decision from menu handler (for backward compatibility)."""
        return self._menu_handler._pending_decision

    @_pending_decision.setter
    def _pending_decision(self, value):
        """Set pending decision in menu handler (for backward compatibility)."""
        self._menu_handler._pending_decision = value

    @property
    def _menu_items(self):
        """Get menu items from menu handler (for backward compatibility)."""
        return self._menu_handler._menu_items

    @_menu_items.setter
    def _menu_items(self, value):
        """Set menu items in menu handler (for backward compatibility)."""
        self._menu_handler._menu_items = value

    # Menu interface - delegates to MenuHandler

    def run_start_menu(self, io_adapter) -> StartDecision:
        """Run the start menu loop until user makes a decision.

        Args:
            io_adapter: PygameIOAdapter instance for event handling and display updates

        Returns:
            StartDecision: The decision made by the user
        """
        return self._menu_handler.run_start_menu(io_adapter)

    def start_menu_loop(self) -> None:
        """Start the menu loop and activate menu state."""
        self._menu_handler.start_menu_loop()

    def is_menu_active(self) -> bool:
        """Check if menu is currently active."""
        return self._menu_handler.is_menu_active()

    def get_pending_decision(self) -> StartDecision | None:
        """Get the pending decision if one has been made."""
        return self._menu_handler.get_pending_decision()

    # Menu callback methods (for backward compatibility)

    def handle_menu_up(self) -> None:
        """Handle UP key in menu."""
        self._menu_handler.handle_menu_up()

    def handle_menu_down(self) -> None:
        """Handle DOWN key in menu."""
        self._menu_handler.handle_menu_down()

    def handle_menu_select(self) -> None:
        """Handle ENTER/SPACE key in menu."""
        self._menu_handler.handle_menu_select()

    def handle_menu_quit(self) -> None:
        """Handle ESCAPE key in menu."""
        self._menu_handler.handle_menu_quit()

    def handle_app_quit(self) -> None:
        """Handle app quit (window close)."""
        self._menu_handler.handle_app_quit()

    # Settings interface - delegates to SettingsHandler

    def run_settings_menu(self, io_adapter, settings) -> SettingsResult:
        """Run the settings menu loop until user confirms or cancels.

        Args:
            io_adapter: PygameIOAdapter instance for event handling and display updates
            settings: GameSettings instance to modify

        Returns:
            SettingsResult: Contains needs_reset and canceled flags
        """
        return self._settings_handler.run_settings_menu(io_adapter, settings)

    # Dialog interface - delegates to DialogHandler

    def prompt_reset_warning(self, io_adapter) -> ResetDecision:
        """Show dialog warning about game reset.

        Args:
            io_adapter: PygameIOAdapter instance for event handling and display updates

        Returns:
            ResetDecision: User's choice (RESET or CANCEL)
        """
        return self._dialog_handler.prompt_reset_warning(io_adapter)

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
        return self._dialog_handler.prompt_game_over(io_adapter, final_score, settings)

    # Command handling interface - delegates to CommandConverter

    def handle_in_game_event(self, event: pygame.event.Event) -> list[Command]:
        """Convert raw pygame event into typed commands.

        Args:
            event: Pygame event to process

        Returns:
            list[Command]: List of commands to apply (may be empty)
        """
        return self._command_converter.handle_in_game_event(event)

    # Additional placeholder methods (for future implementation)

    def handle_pause(self) -> None:
        """Handle pause toggle (called by InputSystem)."""
        # TODO: Implement pause logic
        pass

    def handle_quit(self) -> None:
        """Handle quit request (called by InputSystem)."""
        self._menu_handler._pending_decision = StartDecision.QUIT
        self._menu_handler._menu_active = False

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
        if self._menu_handler.is_menu_active():
            self._menu_handler._render_menu_frame()
