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

"""Tests for UISystem menu navigation and interaction flows."""

import pytest
from unittest.mock import Mock
from ecs.systems.ui import (
    UISystem,
    StartDecision,
    SettingsResult,
    ResetDecision,
    GameOverDecision,
)
from ecs.systems.assets import AssetsSystem
from ecs.world import World


class MockRenderEnqueue:
    """Mock implementation of RenderEnqueue for testing."""

    def __init__(self):
        self.size = (800, 600)
        self.width = 800
        self.height = 600
        self.fill_calls = []
        self.draw_start_menu_calls = []
        self.draw_settings_menu_calls = []
        self.draw_reset_warning_dialog_calls = []
        self.draw_game_over_screen_calls = []

    def fill(self, color):
        self.fill_calls.append(color)

    def draw_start_menu(self, menu_items, selected_index):
        self.draw_start_menu_calls.append((menu_items, selected_index))

    def draw_settings_menu(self, settings_fields, selected_index, settings_values):
        self.draw_settings_menu_calls.append(
            (settings_fields, selected_index, settings_values)
        )

    def draw_reset_warning_dialog(self, selected_option):
        self.draw_reset_warning_dialog_calls.append(selected_option)

    def draw_game_over_screen(self, final_score, selected_option):
        self.draw_game_over_screen_calls.append((final_score, selected_option))


class MockPygameAdapter:
    """Mock pygame adapter for testing."""

    def __init__(self):
        self.events = []
        self.update_display_calls = 0

    def get_events(self):
        return self.events

    def update_display(self):
        self.update_display_calls += 1


@pytest.fixture
def mock_renderer():
    """Create a mock renderer for testing."""
    return MockRenderEnqueue()


@pytest.fixture
def mock_assets():
    """Create a mock assets system for testing."""
    assets = Mock(spec=AssetsSystem)
    assets.get_font.return_value = Mock()
    assets.get_custom_font.return_value = Mock()
    return assets


@pytest.fixture
def mock_pygame_adapter():
    """Create a mock pygame adapter for testing."""
    return MockPygameAdapter()


@pytest.fixture
def ui_system(mock_renderer, mock_assets):
    """Create a UISystem instance for testing."""
    return UISystem(mock_renderer, mock_assets)


@pytest.fixture
def mock_world():
    """Create a mock world for testing."""
    return Mock(spec=World)


class TestUISystemInitialization:
    """Test UISystem initialization and basic properties."""

    def test_initialization(self, mock_renderer, mock_assets):
        """Test UISystem initializes correctly."""
        ui_system = UISystem(mock_renderer, mock_assets)

        assert ui_system._renderer == mock_renderer
        assert ui_system._assets == mock_assets
        assert ui_system._selected_index == 0
        assert ui_system._menu_items == ["Start Game", "Settings"]
        assert ui_system._menu_active is False
        assert ui_system._pending_decision is None

    def test_inherits_from_base_system(self, ui_system):
        """Test UISystem inherits from BaseSystem."""
        from ecs.systems.base_system import BaseSystem

        assert isinstance(ui_system, BaseSystem)


class TestStartMenuNavigation:
    """Test start menu navigation and decision making."""

    def test_menu_callback_up(self, ui_system):
        """Test UP key callback navigation."""
        # Start with first item selected
        ui_system._selected_index = 0
        ui_system._menu_active = True

        # Call the UP callback
        ui_system.handle_menu_up()

        # Should wrap to last item (1)
        assert ui_system._selected_index == 1

    def test_menu_callback_down(self, ui_system):
        """Test DOWN key callback navigation."""
        # Start with first item selected
        ui_system._selected_index = 0
        ui_system._menu_active = True

        # Call the DOWN callback
        ui_system.handle_menu_down()

        # Should move to next item
        assert ui_system._selected_index == 1

    def test_menu_callback_select_start_game(self, ui_system):
        """Test ENTER key callback selects Start Game."""
        # Start with first item selected (Start Game)
        ui_system._selected_index = 0
        ui_system._menu_active = True

        # Call the select callback
        ui_system.handle_menu_select()

        # Should set decision and deactivate menu
        assert ui_system._pending_decision == StartDecision.START_GAME
        assert ui_system._menu_active is False

    def test_menu_callback_select_settings(self, ui_system):
        """Test ENTER key callback selects Settings."""
        # Start with second item selected (Settings)
        ui_system._selected_index = 1
        ui_system._menu_active = True

        # Call the select callback
        ui_system.handle_menu_select()

        # Should set decision and deactivate menu
        assert ui_system._pending_decision == StartDecision.OPEN_SETTINGS
        assert ui_system._menu_active is False

    def test_menu_callback_quit(self, ui_system):
        """Test ESCAPE key callback quits the menu."""
        ui_system._menu_active = True

        # Call the quit callback
        ui_system.handle_menu_quit()

        # Should set decision and deactivate menu
        assert ui_system._pending_decision == StartDecision.QUIT
        assert ui_system._menu_active is False

    def test_menu_callback_app_quit(self, ui_system):
        """Test app quit callback."""
        ui_system._menu_active = True

        # Call the app quit callback
        ui_system.handle_app_quit()

        # Should set decision and deactivate menu
        assert ui_system._pending_decision == StartDecision.QUIT
        assert ui_system._menu_active is False

    def test_menu_callback_ignores_when_inactive(self, ui_system):
        """Test callbacks are ignored when menu is not active."""
        ui_system._menu_active = False
        ui_system._selected_index = 0

        # Call callbacks
        ui_system.handle_menu_up()
        ui_system.handle_menu_down()
        ui_system.handle_menu_select()

        # Should not change anything
        assert ui_system._selected_index == 0
        assert ui_system._pending_decision is None
        assert ui_system._menu_active is False


class TestInGameEventHandling:
    """Test in-game event handling via callbacks."""

    def test_pause_callback(self, ui_system):
        """Test pause callback."""
        # Call the pause callback
        ui_system.handle_pause()

        # Should not raise an exception
        # TODO: Add assertions when pause logic is implemented

    def test_quit_callback(self, ui_system):
        """Test quit callback."""
        ui_system._menu_active = True

        # Call the quit callback
        ui_system.handle_quit()

        # Should set decision and deactivate menu
        assert ui_system._pending_decision == StartDecision.QUIT
        assert ui_system._menu_active is False

    def test_open_settings_callback(self, ui_system):
        """Test open settings callback."""
        # Call the open settings callback
        ui_system.handle_open_settings()

        # Should not raise an exception
        # TODO: Add assertions when settings logic is implemented


class TestSettingsMenu:
    """Test run_settings_menu method."""

    def test_run_settings_menu_exit_without_changes(
        self, ui_system, mock_pygame_adapter
    ):
        """Test settings menu exits with ESC without changes."""
        import pygame

        # Create mock settings
        mock_settings = Mock()
        mock_settings.MENU_FIELDS = [
            {"key": "test_setting", "label": "Test", "type": "int"}
        ]
        mock_settings.get = Mock(return_value=10)

        # Simulate ESC key
        mock_pygame_adapter.events = [Mock(type=pygame.KEYDOWN, key=pygame.K_ESCAPE)]

        # Run menu
        result = ui_system.run_settings_menu(mock_pygame_adapter, mock_settings)

        # Should return with no reset needed and not canceled
        assert isinstance(result, SettingsResult)
        assert result.needs_reset is False
        assert result.canceled is False

    def test_run_settings_menu_exit_with_quit(self, ui_system, mock_pygame_adapter):
        """Test settings menu reverts changes on window close."""
        import pygame

        # Create mock settings
        mock_settings = Mock()
        mock_settings.MENU_FIELDS = [
            {"key": "cells_per_side", "label": "Cells", "type": "int"}
        ]
        # Need enough values for: 5 critical settings snapshot + 1 render call + revert
        mock_settings.get = Mock(return_value=16)
        mock_settings.set = Mock()

        # Simulate QUIT event
        mock_pygame_adapter.events = [Mock(type=pygame.QUIT)]

        # Run menu
        result = ui_system.run_settings_menu(mock_pygame_adapter, mock_settings)

        # Should revert changes and return canceled
        assert result.canceled is True
        assert mock_settings.set.call_count >= 5  # Should revert critical settings

    def test_run_settings_menu_navigation(self, ui_system, mock_pygame_adapter):
        """Test settings menu navigation keys."""
        import pygame

        # Create mock settings with multiple fields
        mock_settings = Mock()
        mock_settings.MENU_FIELDS = [
            {"key": "setting1", "label": "Setting 1", "type": "int"},
            {"key": "setting2", "label": "Setting 2", "type": "int"},
        ]
        mock_settings.get = Mock(return_value=10)
        mock_settings.step_setting = Mock()

        # Simulate: DOWN, UP, LEFT, RIGHT, ENTER
        mock_pygame_adapter.events = [
            Mock(type=pygame.KEYDOWN, key=pygame.K_DOWN),
            Mock(type=pygame.KEYDOWN, key=pygame.K_UP),
            Mock(type=pygame.KEYDOWN, key=pygame.K_LEFT),
            Mock(type=pygame.KEYDOWN, key=pygame.K_RIGHT),
            Mock(type=pygame.KEYDOWN, key=pygame.K_RETURN),
        ]

        # Run menu
        ui_system.run_settings_menu(mock_pygame_adapter, mock_settings)

        # Should have called step_setting for LEFT and RIGHT
        assert mock_settings.step_setting.call_count == 2


class TestResetWarning:
    """Test prompt_reset_warning method."""

    def test_prompt_reset_warning_selects_reset(self, ui_system, mock_pygame_adapter):
        """Test reset warning returns RESET when user confirms."""
        import pygame

        # Simulate ENTER on first option (Reset Now)
        mock_pygame_adapter.events = [Mock(type=pygame.KEYDOWN, key=pygame.K_RETURN)]

        # Run dialog
        result = ui_system.prompt_reset_warning(mock_pygame_adapter)

        # Should return RESET
        assert result == ResetDecision.RESET

    def test_prompt_reset_warning_selects_cancel(self, ui_system, mock_pygame_adapter):
        """Test reset warning returns CANCEL when user cancels."""
        import pygame

        # Simulate DOWN then ENTER (select Cancel Changes)
        mock_pygame_adapter.events = [
            Mock(type=pygame.KEYDOWN, key=pygame.K_DOWN),
            Mock(type=pygame.KEYDOWN, key=pygame.K_RETURN),
        ]

        # Run dialog
        result = ui_system.prompt_reset_warning(mock_pygame_adapter)

        # Should return CANCEL
        assert result == ResetDecision.CANCEL

    def test_prompt_reset_warning_esc_cancels(self, ui_system, mock_pygame_adapter):
        """Test reset warning returns CANCEL when user presses ESC."""
        import pygame

        # Simulate ESC
        mock_pygame_adapter.events = [Mock(type=pygame.KEYDOWN, key=pygame.K_ESCAPE)]

        # Run dialog
        result = ui_system.prompt_reset_warning(mock_pygame_adapter)

        # Should return CANCEL
        assert result == ResetDecision.CANCEL

    def test_prompt_reset_warning_quit_cancels(self, ui_system, mock_pygame_adapter):
        """Test reset warning returns CANCEL when user closes window."""
        import pygame

        # Simulate window close
        mock_pygame_adapter.events = [Mock(type=pygame.QUIT)]

        # Run dialog
        result = ui_system.prompt_reset_warning(mock_pygame_adapter)

        # Should return CANCEL
        assert result == ResetDecision.CANCEL


class TestGameOver:
    """Test prompt_game_over method."""

    def test_prompt_game_over_restart(self, ui_system, mock_pygame_adapter):
        """Test game over returns RESTART when user presses ENTER."""
        import pygame

        # Simulate ENTER
        mock_pygame_adapter.events = [Mock(type=pygame.KEYDOWN, key=pygame.K_RETURN)]

        # Run dialog
        result = ui_system.prompt_game_over(mock_pygame_adapter, 100)

        # Should return RESTART
        assert result == GameOverDecision.RESTART

    def test_prompt_game_over_restart_with_space(self, ui_system, mock_pygame_adapter):
        """Test game over returns RESTART when user presses SPACE."""
        import pygame

        # Simulate SPACE
        mock_pygame_adapter.events = [Mock(type=pygame.KEYDOWN, key=pygame.K_SPACE)]

        # Run dialog
        result = ui_system.prompt_game_over(mock_pygame_adapter, 100)

        # Should return RESTART
        assert result == GameOverDecision.RESTART

    def test_prompt_game_over_quit(self, ui_system, mock_pygame_adapter):
        """Test game over returns QUIT when user presses Q."""
        import pygame

        # Simulate Q key
        mock_pygame_adapter.events = [Mock(type=pygame.KEYDOWN, key=pygame.K_q)]

        # Run dialog
        result = ui_system.prompt_game_over(mock_pygame_adapter, 100)

        # Should return QUIT
        assert result == GameOverDecision.QUIT

    def test_prompt_game_over_quit_on_window_close(
        self, ui_system, mock_pygame_adapter
    ):
        """Test game over returns QUIT when user closes window."""
        import pygame

        # Simulate window close
        mock_pygame_adapter.events = [Mock(type=pygame.QUIT)]

        # Run dialog
        result = ui_system.prompt_game_over(mock_pygame_adapter, 100)

        # Should return QUIT
        assert result == GameOverDecision.QUIT

    def test_prompt_game_over_with_settings(self, ui_system, mock_pygame_adapter):
        """Test game over works with settings parameter."""
        import pygame

        # Create mock settings
        mock_settings = Mock()
        mock_settings.get = Mock(return_value=True)

        # Simulate ENTER
        mock_pygame_adapter.events = [Mock(type=pygame.KEYDOWN, key=pygame.K_RETURN)]

        # Run dialog with settings
        result = ui_system.prompt_game_over(mock_pygame_adapter, 100, mock_settings)

        # Should return RESTART
        assert result == GameOverDecision.RESTART


class TestOtherMenuMethods:
    """Test other menu methods."""

    def test_apply_settings_placeholder(self, ui_system):
        """Test settings application is placeholder."""
        # Should not raise an exception
        ui_system.apply_settings(reset_objects=True)
        ui_system.apply_settings(reset_objects=False)

    def test_needs_reset_placeholder(self, ui_system):
        """Test reset detection returns placeholder result."""
        result = ui_system.needs_reset()

        assert result is False


class TestMenuLoopMethods:
    """Test menu loop management methods."""

    def test_start_menu_loop_activates_menu(self, ui_system):
        """Test start_menu_loop activates menu state."""
        ui_system._menu_active = False
        ui_system._selected_index = 5

        # Start menu loop
        ui_system.start_menu_loop()

        # Should activate menu and reset state
        assert ui_system._menu_active is True
        assert ui_system._selected_index == 0
        assert ui_system._pending_decision is None

    def test_is_menu_active_returns_correct_state(self, ui_system):
        """Test is_menu_active returns correct state."""
        ui_system._menu_active = True
        assert ui_system.is_menu_active() is True

        ui_system._menu_active = False
        assert ui_system.is_menu_active() is False

    def test_get_pending_decision_returns_decision(self, ui_system):
        """Test get_pending_decision returns pending decision."""
        ui_system._pending_decision = StartDecision.START_GAME
        assert ui_system.get_pending_decision() == StartDecision.START_GAME

        ui_system._pending_decision = None
        assert ui_system.get_pending_decision() is None


class TestRunStartMenu:
    """Test run_start_menu method."""

    def test_run_start_menu_returns_start_game_decision(
        self, ui_system, mock_pygame_adapter
    ):
        """Test run_start_menu returns START_GAME when user selects start."""
        import pygame

        # Simulate user pressing ENTER on first item
        mock_pygame_adapter.events = [Mock(type=pygame.KEYDOWN, key=pygame.K_RETURN)]

        # Run menu
        decision = ui_system.run_start_menu(mock_pygame_adapter)

        # Should return START_GAME
        assert decision == StartDecision.START_GAME
        assert ui_system._menu_active is False

    def test_run_start_menu_returns_settings_decision(
        self, ui_system, mock_pygame_adapter
    ):
        """Test run_start_menu returns OPEN_SETTINGS when user selects settings."""
        import pygame

        # Simulate user pressing DOWN then ENTER
        mock_pygame_adapter.events = [
            Mock(type=pygame.KEYDOWN, key=pygame.K_DOWN),
            Mock(type=pygame.KEYDOWN, key=pygame.K_RETURN),
        ]

        # Run menu with DOWN->ENTER sequence
        decision = ui_system.run_start_menu(mock_pygame_adapter)

        assert decision == StartDecision.OPEN_SETTINGS
        assert ui_system._menu_active is False

    def test_run_start_menu_returns_quit_decision(self, ui_system, mock_pygame_adapter):
        """Test run_start_menu returns QUIT when user presses ESC."""
        import pygame

        # Simulate user pressing ESC
        mock_pygame_adapter.events = [Mock(type=pygame.KEYDOWN, key=pygame.K_ESCAPE)]

        # Run menu
        decision = ui_system.run_start_menu(mock_pygame_adapter)

        # Should return QUIT
        assert decision == StartDecision.QUIT
        assert ui_system._menu_active is False

    def test_run_start_menu_returns_quit_on_window_close(
        self, ui_system, mock_pygame_adapter
    ):
        """Test run_start_menu returns QUIT when user closes window."""
        import pygame

        # Simulate user closing window
        mock_pygame_adapter.events = [Mock(type=pygame.QUIT)]

        # Run menu
        decision = ui_system.run_start_menu(mock_pygame_adapter)

        # Should return QUIT
        assert decision == StartDecision.QUIT
        assert ui_system._menu_active is False

    def test_run_start_menu_handles_navigation_keys(
        self, ui_system, mock_pygame_adapter
    ):
        """Test run_start_menu properly handles all navigation keys."""
        import pygame

        # Simulate complex navigation: DOWN, UP, W, S, SPACE
        mock_pygame_adapter.events = [
            Mock(type=pygame.KEYDOWN, key=pygame.K_DOWN),  # Move to Settings
        ]

        ui_system.start_menu_loop()
        ui_system.handle_menu_down()
        assert ui_system._selected_index == 1

        # Now move back up with W key
        ui_system.handle_menu_up()
        assert ui_system._selected_index == 0

        # Select with SPACE
        ui_system.handle_menu_select()
        assert ui_system._pending_decision == StartDecision.START_GAME

    def test_run_start_menu_calls_renderer(self, ui_system, mock_pygame_adapter):
        """Test run_start_menu calls renderer methods."""
        import pygame

        # Simulate quick menu exit
        mock_pygame_adapter.events = [Mock(type=pygame.KEYDOWN, key=pygame.K_ESCAPE)]

        # Mock renderer methods
        fill_mock = Mock()
        draw_mock = Mock()
        ui_system._renderer.fill = fill_mock
        ui_system._renderer.draw_start_menu = draw_mock

        # Run menu
        ui_system.run_start_menu(mock_pygame_adapter)

        # Should have called renderer methods at least once
        assert fill_mock.call_count >= 1
        assert draw_mock.call_count >= 1

    def test_run_start_menu_updates_display(self, ui_system, mock_pygame_adapter):
        """Test run_start_menu calls update_display."""
        import pygame

        # Simulate quick menu exit
        mock_pygame_adapter.events = [Mock(type=pygame.KEYDOWN, key=pygame.K_ESCAPE)]

        # Run menu
        ui_system.run_start_menu(mock_pygame_adapter)

        # Should have called update_display at least once
        assert mock_pygame_adapter.update_display_calls >= 1


class TestUISystemUpdate:
    """Test UISystem update method."""

    def test_update_renders_when_menu_active(
        self, ui_system, mock_world, mock_renderer
    ):
        """Test update method renders when menu is active."""
        ui_system._menu_active = True

        # Mock the renderer methods
        ui_system._renderer.fill = Mock()
        ui_system._renderer.draw_start_menu = Mock()

        # Call update
        ui_system.update(mock_world)

        # Should have called render methods
        ui_system._renderer.fill.assert_called_once()
        ui_system._renderer.draw_start_menu.assert_called_once()

    def test_update_does_nothing_when_menu_inactive(
        self, ui_system, mock_world, mock_renderer
    ):
        """Test update method does nothing when menu is inactive."""
        ui_system._menu_active = False

        # Mock the renderer methods
        ui_system._renderer.fill = Mock()
        ui_system._renderer.draw_start_menu = Mock()

        # Call update
        ui_system.update(mock_world)

        # Should not have called render methods
        ui_system._renderer.fill.assert_not_called()
        ui_system._renderer.draw_start_menu.assert_not_called()


class TestDecisionEnums:
    """Test decision enum values and behavior."""

    def test_start_decision_values(self):
        """Test StartDecision enum values."""
        assert StartDecision.START_GAME.value == "start_game"
        assert StartDecision.OPEN_SETTINGS.value == "open_settings"
        assert StartDecision.QUIT.value == "quit"

    def test_reset_decision_values(self):
        """Test ResetDecision enum values."""
        assert ResetDecision.RESET.value == "reset"
        assert ResetDecision.CANCEL.value == "cancel"

    def test_game_over_decision_values(self):
        """Test GameOverDecision enum values."""
        assert GameOverDecision.RESTART.value == "restart"
        assert GameOverDecision.QUIT.value == "quit"


class TestSettingsResult:
    """Test SettingsResult class."""

    def test_settings_result_default_values(self):
        """Test SettingsResult default values."""
        result = SettingsResult()

        assert result.needs_reset is False
        assert result.canceled is False

    def test_settings_result_custom_values(self):
        """Test SettingsResult with custom values."""
        result = SettingsResult(needs_reset=True, canceled=True)

        assert result.needs_reset is True
        assert result.canceled is True
