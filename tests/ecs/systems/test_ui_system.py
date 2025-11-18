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
    StartDecision,
    SettingsResult,
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
def mock_world():
    """Create a mock world for testing."""
    return Mock(spec=World)


class TestDecisionEnums:
    """Test decision enum values and behavior."""

    def test_start_decision_values(self):
        """Test StartDecision enum values."""
        assert StartDecision.START_GAME.value == "start_game"
        assert StartDecision.OPEN_SETTINGS.value == "open_settings"
        assert StartDecision.QUIT.value == "quit"


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
