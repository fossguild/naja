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

"""Tests for UISystem menu navigation and interaction flows."""

import pytest
from unittest.mock import Mock
from src.ecs.systems.ui_system import (
    UISystem,
    StartDecision,
    SettingsResult,
    ResetDecision,
    GameOverDecision,
)
from src.ecs.systems.assets import AssetsSystem
from src.ecs.world import World


class MockRenderEnqueue:
    """Mock implementation of RenderEnqueue for testing."""

    def __init__(self):
        self.size = (800, 600)
        self.width = 800
        self.height = 600
        self.fill_calls = []
        self.draw_start_menu_calls = []

    def fill(self, color):
        self.fill_calls.append(color)

    def draw_start_menu(self, menu_items, selected_index):
        self.draw_start_menu_calls.append((menu_items, selected_index))


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
        from src.ecs.systems.base_system import BaseSystem

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


class TestOtherMenuMethods:
    """Test other menu methods (placeholders for now)."""

    def test_run_settings_menu_placeholder(self, ui_system):
        """Test settings menu returns placeholder result."""
        result = ui_system.run_settings_menu()

        assert isinstance(result, SettingsResult)
        assert result.needs_reset is False
        assert result.canceled is True

    def test_prompt_reset_warning_placeholder(self, ui_system):
        """Test reset warning returns placeholder result."""
        result = ui_system.prompt_reset_warning()

        assert result == ResetDecision.CANCEL

    def test_prompt_game_over_placeholder(self, ui_system):
        """Test game over prompt returns placeholder result."""
        result = ui_system.prompt_game_over(100)

        assert result == GameOverDecision.RESTART

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
