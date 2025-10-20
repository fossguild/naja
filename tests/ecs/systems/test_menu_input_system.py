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

"""Tests for MenuInputSystem input routing and callback delegation."""

import pytest
import pygame
from unittest.mock import Mock
from src.ecs.systems.menu_input_system import MenuInputSystem
from src.ecs.world import World


class MockPygameAdapter:
    """Mock pygame adapter for testing."""

    def __init__(self):
        self.events = []

    def get_events(self):
        return self.events


class MockUISystem:
    """Mock UI system for testing callbacks."""

    def __init__(self):
        self.callbacks_called = []

    def handle_menu_up(self):
        self.callbacks_called.append("handle_menu_up")

    def handle_menu_down(self):
        self.callbacks_called.append("handle_menu_down")

    def handle_menu_select(self):
        self.callbacks_called.append("handle_menu_select")

    def handle_menu_quit(self):
        self.callbacks_called.append("handle_menu_quit")

    def handle_app_quit(self):
        self.callbacks_called.append("handle_app_quit")

    def handle_quit(self):
        self.callbacks_called.append("handle_quit")


@pytest.fixture
def mock_pygame_adapter():
    """Create a mock pygame adapter for testing."""
    return MockPygameAdapter()


@pytest.fixture
def mock_ui_system():
    """Create a mock UI system for testing."""
    return MockUISystem()


@pytest.fixture
def menu_input_system(mock_pygame_adapter, mock_ui_system):
    """Create a MenuInputSystem instance for testing."""
    return MenuInputSystem(mock_pygame_adapter, mock_ui_system)


@pytest.fixture
def mock_world():
    """Create a mock world for testing."""
    return Mock(spec=World)


class TestMenuInputSystemInitialization:
    """Test MenuInputSystem initialization."""

    def test_initialization(self, mock_pygame_adapter, mock_ui_system):
        """Test MenuInputSystem initializes correctly."""
        system = MenuInputSystem(mock_pygame_adapter, mock_ui_system)

        assert system._pygame_adapter == mock_pygame_adapter
        assert system._ui_system == mock_ui_system

    def test_inherits_from_base_system(self, menu_input_system):
        """Test MenuInputSystem inherits from BaseSystem."""
        from src.ecs.systems.base_system import BaseSystem

        assert isinstance(menu_input_system, BaseSystem)


class TestMenuInputSystemEventHandling:
    """Test menu input event handling and callback routing."""

    def test_handles_up_key(
        self, menu_input_system, mock_pygame_adapter, mock_ui_system, mock_world
    ):
        """Test UP key calls handle_menu_up callback."""
        # Simulate UP key press
        up_event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_UP)
        mock_pygame_adapter.events = [up_event]

        # Process events
        menu_input_system.update(mock_world)

        # Should have called the callback
        assert "handle_menu_up" in mock_ui_system.callbacks_called

    def test_handles_down_key(
        self, menu_input_system, mock_pygame_adapter, mock_ui_system, mock_world
    ):
        """Test DOWN key calls handle_menu_down callback."""
        # Simulate DOWN key press
        down_event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_DOWN)
        mock_pygame_adapter.events = [down_event]

        # Process events
        menu_input_system.update(mock_world)

        # Should have called the callback
        assert "handle_menu_down" in mock_ui_system.callbacks_called

    def test_handles_enter_key(
        self, menu_input_system, mock_pygame_adapter, mock_ui_system, mock_world
    ):
        """Test ENTER key calls handle_menu_select callback."""
        # Simulate ENTER key press
        enter_event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN)
        mock_pygame_adapter.events = [enter_event]

        # Process events
        menu_input_system.update(mock_world)

        # Should have called the callback
        assert "handle_menu_select" in mock_ui_system.callbacks_called

    def test_handles_space_key(
        self, menu_input_system, mock_pygame_adapter, mock_ui_system, mock_world
    ):
        """Test SPACE key calls handle_menu_select callback."""
        # Simulate SPACE key press
        space_event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE)
        mock_pygame_adapter.events = [space_event]

        # Process events
        menu_input_system.update(mock_world)

        # Should have called the callback
        assert "handle_menu_select" in mock_ui_system.callbacks_called

    def test_handles_escape_key(
        self, menu_input_system, mock_pygame_adapter, mock_ui_system, mock_world
    ):
        """Test ESCAPE key calls handle_menu_quit callback."""
        # Simulate ESCAPE key press
        escape_event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE)
        mock_pygame_adapter.events = [escape_event]

        # Process events
        menu_input_system.update(mock_world)

        # Should have called the callback
        assert "handle_menu_quit" in mock_ui_system.callbacks_called

    def test_handles_q_key(
        self, menu_input_system, mock_pygame_adapter, mock_ui_system, mock_world
    ):
        """Test Q key calls handle_quit callback."""
        # Simulate Q key press
        q_event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_q)
        mock_pygame_adapter.events = [q_event]

        # Process events
        menu_input_system.update(mock_world)

        # Should have called the callback
        assert "handle_quit" in mock_ui_system.callbacks_called

    def test_handles_quit_event(
        self, menu_input_system, mock_pygame_adapter, mock_ui_system, mock_world
    ):
        """Test QUIT event calls handle_app_quit callback."""
        # Simulate QUIT event
        quit_event = pygame.event.Event(pygame.QUIT)
        mock_pygame_adapter.events = [quit_event]

        # Process events
        menu_input_system.update(mock_world)

        # Should have called the callback
        assert "handle_app_quit" in mock_ui_system.callbacks_called

    def test_handles_alternative_keys(
        self, menu_input_system, mock_pygame_adapter, mock_ui_system, mock_world
    ):
        """Test alternative key mappings (WASD)."""
        # Test W key (alternative UP)
        w_event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_w)
        mock_pygame_adapter.events = [w_event]
        menu_input_system.update(mock_world)
        assert "handle_menu_up" in mock_ui_system.callbacks_called

        # Test S key (alternative DOWN)
        mock_ui_system.callbacks_called.clear()
        s_event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_s)
        mock_pygame_adapter.events = [s_event]
        menu_input_system.update(mock_world)
        assert "handle_menu_down" in mock_ui_system.callbacks_called

    def test_ignores_unknown_keys(
        self, menu_input_system, mock_pygame_adapter, mock_ui_system, mock_world
    ):
        """Test unknown keys are ignored."""
        # Simulate unknown key press
        unknown_event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_x)
        mock_pygame_adapter.events = [unknown_event]

        # Process events
        menu_input_system.update(mock_world)

        # Should not have called any callbacks
        assert len(mock_ui_system.callbacks_called) == 0

    def test_handles_multiple_events(
        self, menu_input_system, mock_pygame_adapter, mock_ui_system, mock_world
    ):
        """Test multiple events in sequence."""
        # Simulate multiple key presses
        up_event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_UP)
        down_event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_DOWN)
        enter_event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN)
        mock_pygame_adapter.events = [up_event, down_event, enter_event]

        # Process events
        menu_input_system.update(mock_world)

        # Should have called all callbacks
        assert "handle_menu_up" in mock_ui_system.callbacks_called
        assert "handle_menu_down" in mock_ui_system.callbacks_called
        assert "handle_menu_select" in mock_ui_system.callbacks_called
        assert len(mock_ui_system.callbacks_called) == 3


class TestMenuInputSystemEdgeCases:
    """Test edge cases and error handling."""

    def test_handles_no_events(
        self, menu_input_system, mock_pygame_adapter, mock_ui_system, mock_world
    ):
        """Test system handles empty event list."""
        mock_pygame_adapter.events = []

        # Process events
        menu_input_system.update(mock_world)

        # Should not have called any callbacks
        assert len(mock_ui_system.callbacks_called) == 0

    def test_handles_no_pygame_adapter(self, mock_ui_system, mock_world):
        """Test system handles missing pygame adapter."""
        system = MenuInputSystem(None, mock_ui_system)

        # Should not raise an exception
        system.update(mock_world)

        # Should not have called any callbacks
        assert len(mock_ui_system.callbacks_called) == 0

    def test_handles_no_ui_system(self, mock_pygame_adapter, mock_world):
        """Test system handles missing UI system."""
        system = MenuInputSystem(mock_pygame_adapter, None)

        # Add an event
        up_event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_UP)
        mock_pygame_adapter.events = [up_event]

        # Should not raise an exception
        system.update(mock_world)

    def test_mouse_click_ignored(
        self, menu_input_system, mock_pygame_adapter, mock_ui_system, mock_world
    ):
        """Test mouse clicks are ignored (placeholder for future implementation)."""
        # Simulate mouse click
        mouse_event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1)
        mock_pygame_adapter.events = [mouse_event]

        # Process events
        menu_input_system.update(mock_world)

        # Should not have called any callbacks
        assert len(mock_ui_system.callbacks_called) == 0
