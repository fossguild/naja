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

"""UISystem - handles all user interaction flows and menu navigation.

DEPRECATED: This file is legacy test code. The actual game uses scene-based
architecture (MenuScene, GameplayScene, etc.). Kept for backward compatibility
with existing tests.
"""

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
    """Legacy test system for UI state management and menu logic.

    DEPRECATED: Use scene-based architecture instead.
    """

    def __init__(self, renderer: RenderEnqueue, assets: AssetsSystem):
        self._renderer = renderer
        self._assets = assets
        self._selected_index = 0
        self._menu_items = ["Start Game", "Settings"]
        self._setting_snapshots = {}
        self._menu_active = False
        self._pending_decision = None

    def run_start_menu(self, io_adapter) -> StartDecision:
        """Run start menu loop until user decides."""
        self.start_menu_loop()
        while self._pending_decision is None:
            self._render_menu_frame()
            io_adapter.update_display()
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
        """Activate menu state."""
        self._selected_index = 0
        self._menu_active = True
        self._pending_decision = None
        self._render_menu_frame()

    def is_menu_active(self) -> bool:
        """Check if menu is active."""
        return self._menu_active

    def get_pending_decision(self) -> StartDecision | None:
        """Get pending decision if one was made."""
        return self._pending_decision

    def _render_menu_frame(self) -> None:
        """Render current menu frame."""
        self._renderer.fill((32, 32, 32))
        self._renderer.draw_start_menu(self._menu_items, self._selected_index)

    def handle_menu_up(self) -> None:
        """Handle UP key."""
        if self._menu_active:
            self._selected_index = (self._selected_index - 1) % len(self._menu_items)

    def handle_menu_down(self) -> None:
        """Handle DOWN key."""
        if self._menu_active:
            self._selected_index = (self._selected_index + 1) % len(self._menu_items)

    def handle_menu_select(self) -> None:
        """Handle ENTER/SPACE key."""
        if self._menu_active:
            selected_item = self._menu_items[self._selected_index]
            if selected_item == "Start Game":
                self._pending_decision = StartDecision.START_GAME
                self._menu_active = False
            elif selected_item == "Settings":
                self._pending_decision = StartDecision.OPEN_SETTINGS
                self._menu_active = False

    def handle_menu_quit(self) -> None:
        """Handle ESCAPE key."""
        if self._menu_active:
            self._pending_decision = StartDecision.QUIT
            self._menu_active = False

    def handle_app_quit(self) -> None:
        """Handle app quit."""
        self._pending_decision = StartDecision.QUIT
        self._menu_active = False

    def run_settings_menu(self, io_adapter, settings) -> SettingsResult:
        """Run settings menu loop."""
        selected_index = 0
        critical = [
            "cells_per_side",
            "obstacle_difficulty",
            "initial_speed",
            "number_of_apples",
            "electric_walls",
        ]
        original = {k: settings.get(k) for k in critical}

        while True:
            values = {f["key"]: settings.get(f["key"]) for f in settings.MENU_FIELDS}
            self._renderer.draw_settings_menu(
                settings.MENU_FIELDS, selected_index, values
            )
            io_adapter.update_display()

            for event in io_adapter.get_events():
                if event.type == pygame.QUIT:
                    for k, v in original.items():
                        settings.set(k, v)
                    return SettingsResult(needs_reset=False, canceled=True)

                if event.type == pygame.KEYDOWN:
                    key = event.key
                    if key in (pygame.K_ESCAPE, pygame.K_RETURN):
                        needs_reset = any(
                            settings.get(k) != original[k] for k in critical
                        )
                        return SettingsResult(needs_reset=needs_reset, canceled=False)
                    elif key in (pygame.K_DOWN, pygame.K_s):
                        selected_index = (selected_index + 1) % len(
                            settings.MENU_FIELDS
                        )
                    elif key in (pygame.K_UP, pygame.K_w):
                        selected_index = (selected_index - 1) % len(
                            settings.MENU_FIELDS
                        )
                    elif key in (pygame.K_LEFT, pygame.K_a):
                        settings.step_setting(settings.MENU_FIELDS[selected_index], -1)
                    elif key in (pygame.K_RIGHT, pygame.K_d):
                        settings.step_setting(settings.MENU_FIELDS[selected_index], +1)
                    elif key == pygame.K_c:
                        settings.randomize_colors()

    def prompt_reset_warning(self, io_adapter) -> ResetDecision:
        """Show reset warning dialog."""
        selected = 0
        while True:
            self._renderer.draw_reset_warning_dialog(selected)
            io_adapter.update_display()

            for event in io_adapter.get_events():
                if event.type == pygame.QUIT:
                    return ResetDecision.CANCEL
                if event.type == pygame.KEYDOWN:
                    key = event.key
                    if key in (pygame.K_UP, pygame.K_w):
                        selected = (selected - 1) % 2
                    elif key in (pygame.K_DOWN, pygame.K_s):
                        selected = (selected + 1) % 2
                    elif key in (pygame.K_RETURN, pygame.K_SPACE):
                        return (
                            ResetDecision.RESET
                            if selected == 0
                            else ResetDecision.CANCEL
                        )
                    elif key == pygame.K_ESCAPE:
                        return ResetDecision.CANCEL

    def prompt_game_over(
        self, io_adapter, final_score: int, settings=None
    ) -> GameOverDecision:
        """Show game over screen."""
        selected_option = 0
        while True:
            self._renderer.draw_game_over_screen(final_score, selected_option)
            io_adapter.update_display()

            for event in io_adapter.get_events():
                if event.type == pygame.QUIT:
                    return GameOverDecision.QUIT
                if event.type == pygame.KEYDOWN:
                    key = event.key
                    if key in (pygame.K_RETURN, pygame.K_SPACE):
                        return GameOverDecision.RESTART
                    elif key == pygame.K_q:
                        return GameOverDecision.QUIT

    def handle_pause(self) -> None:
        """Handle pause toggle."""
        pass

    def handle_quit(self) -> None:
        """Handle quit request."""
        self._pending_decision = StartDecision.QUIT
        self._menu_active = False

    def handle_open_settings(self) -> None:
        """Handle open settings request."""
        pass

    def apply_settings(self, reset_objects: bool = False) -> None:
        """Apply pending settings changes."""
        pass

    def needs_reset(self) -> bool:
        """Check if settings require game reset."""
        return False

    def update(self, world: World) -> None:
        """Update UI state."""
        if self._menu_active:
            self._render_menu_frame()
