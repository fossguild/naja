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

"""Tests for InputSystem."""

import pytest
from unittest.mock import Mock
import pygame

from src.ecs.systems.input import InputSystem
from src.ecs.world import World
from src.ecs.board import Board


@pytest.fixture
def world():
    """Create a test world."""
    board = Board(20, 20)
    return World(board)


@pytest.fixture
def mock_pygame_adapter():
    """Create a mock pygame adapter."""
    adapter = Mock()
    adapter.get_events = Mock(return_value=[])
    return adapter


@pytest.fixture
def mock_callbacks():
    """Create mock callback functions."""
    return {
        "direction": Mock(),
        "get_current_direction": Mock(return_value=(0, 0)),
        "quit": Mock(),
        "pause": Mock(),
        "menu": Mock(),
        "music_toggle": Mock(),
        "palette_randomize": Mock(),
    }


def test_input_system_creation(mock_pygame_adapter, mock_callbacks):
    """Test that InputSystem can be created with all callbacks."""
    system = InputSystem(
        pygame_adapter=mock_pygame_adapter,
        direction_callback=mock_callbacks["direction"],
        get_current_direction_callback=mock_callbacks["get_current_direction"],
        quit_callback=mock_callbacks["quit"],
        pause_callback=mock_callbacks["pause"],
        menu_callback=mock_callbacks["menu"],
        music_toggle_callback=mock_callbacks["music_toggle"],
        palette_randomize_callback=mock_callbacks["palette_randomize"],
    )

    assert system is not None
    assert system._pygame_adapter == mock_pygame_adapter


def test_input_system_handles_no_events(world, mock_pygame_adapter, mock_callbacks):
    """Test that InputSystem handles empty event list gracefully."""
    mock_pygame_adapter.get_events.return_value = []

    system = InputSystem(
        pygame_adapter=mock_pygame_adapter,
        direction_callback=mock_callbacks["direction"],
        get_current_direction_callback=mock_callbacks["get_current_direction"],
    )

    system.update(world)

    # no callbacks should be triggered
    mock_callbacks["direction"].assert_not_called()


def test_input_system_handles_quit_event(world, mock_pygame_adapter, mock_callbacks):
    """Test that InputSystem calls quit callback on QUIT event."""
    quit_event = Mock()
    quit_event.type = pygame.QUIT
    mock_pygame_adapter.get_events.return_value = [quit_event]

    system = InputSystem(
        pygame_adapter=mock_pygame_adapter,
        quit_callback=mock_callbacks["quit"],
    )

    system.update(world)

    mock_callbacks["quit"].assert_called_once()


def test_input_system_handles_direction_keys(
    world, mock_pygame_adapter, mock_callbacks
):
    """Test that InputSystem handles arrow and WASD keys."""
    test_cases = [
        (pygame.K_DOWN, 0, 1),
        (pygame.K_UP, 0, -1),
        (pygame.K_RIGHT, 1, 0),
        (pygame.K_LEFT, -1, 0),
        (pygame.K_s, 0, 1),
        (pygame.K_w, 0, -1),
        (pygame.K_d, 1, 0),
        (pygame.K_a, -1, 0),
    ]

    for key, expected_dx, expected_dy in test_cases:
        mock_callbacks["direction"].reset_mock()

        keydown_event = Mock()
        keydown_event.type = pygame.KEYDOWN
        keydown_event.key = key
        mock_pygame_adapter.get_events.return_value = [keydown_event]

        system = InputSystem(
            pygame_adapter=mock_pygame_adapter,
            direction_callback=mock_callbacks["direction"],
        )

        system.update(world)

        mock_callbacks["direction"].assert_called_once_with(expected_dx, expected_dy)


def test_input_system_handles_pause_key(world, mock_pygame_adapter, mock_callbacks):
    """Test that InputSystem handles P key for pause."""
    keydown_event = Mock()
    keydown_event.type = pygame.KEYDOWN
    keydown_event.key = pygame.K_p
    mock_pygame_adapter.get_events.return_value = [keydown_event]

    system = InputSystem(
        pygame_adapter=mock_pygame_adapter,
        pause_callback=mock_callbacks["pause"],
    )

    system.update(world)

    mock_callbacks["pause"].assert_called_once()


def test_input_system_handles_quit_key(world, mock_pygame_adapter, mock_callbacks):
    """Test that InputSystem handles Q key for quit."""
    keydown_event = Mock()
    keydown_event.type = pygame.KEYDOWN
    keydown_event.key = pygame.K_q
    mock_pygame_adapter.get_events.return_value = [keydown_event]

    system = InputSystem(
        pygame_adapter=mock_pygame_adapter,
        quit_callback=mock_callbacks["quit"],
    )

    system.update(world)

    mock_callbacks["quit"].assert_called_once()


def test_input_system_handles_menu_keys(world, mock_pygame_adapter, mock_callbacks):
    """Test that InputSystem handles M and ESC keys for menu."""
    for menu_key in [pygame.K_m, pygame.K_ESCAPE]:
        mock_callbacks["menu"].reset_mock()

        keydown_event = Mock()
        keydown_event.type = pygame.KEYDOWN
        keydown_event.key = menu_key
        mock_pygame_adapter.get_events.return_value = [keydown_event]

        system = InputSystem(
            pygame_adapter=mock_pygame_adapter,
            menu_callback=mock_callbacks["menu"],
        )

        system.update(world)

        mock_callbacks["menu"].assert_called_once()


def test_input_system_handles_music_toggle_key(
    world, mock_pygame_adapter, mock_callbacks
):
    """Test that InputSystem handles N key for music toggle."""
    keydown_event = Mock()
    keydown_event.type = pygame.KEYDOWN
    keydown_event.key = pygame.K_n
    mock_pygame_adapter.get_events.return_value = [keydown_event]

    system = InputSystem(
        pygame_adapter=mock_pygame_adapter,
        music_toggle_callback=mock_callbacks["music_toggle"],
    )

    system.update(world)

    mock_callbacks["music_toggle"].assert_called_once()


def test_input_system_handles_palette_randomize_key(
    world, mock_pygame_adapter, mock_callbacks
):
    """Test that InputSystem handles C key for palette randomize."""
    keydown_event = Mock()
    keydown_event.type = pygame.KEYDOWN
    keydown_event.key = pygame.K_c
    mock_pygame_adapter.get_events.return_value = [keydown_event]

    system = InputSystem(
        pygame_adapter=mock_pygame_adapter,
        palette_randomize_callback=mock_callbacks["palette_randomize"],
    )

    system.update(world)

    mock_callbacks["palette_randomize"].assert_called_once()


def test_input_system_handles_multiple_events(
    world, mock_pygame_adapter, mock_callbacks
):
    """Test that InputSystem processes multiple events in one update."""
    event1 = Mock()
    event1.type = pygame.KEYDOWN
    event1.key = pygame.K_p

    event2 = Mock()
    event2.type = pygame.KEYDOWN
    event2.key = pygame.K_w

    mock_pygame_adapter.get_events.return_value = [event1, event2]

    system = InputSystem(
        pygame_adapter=mock_pygame_adapter,
        direction_callback=mock_callbacks["direction"],
        pause_callback=mock_callbacks["pause"],
    )

    system.update(world)

    mock_callbacks["pause"].assert_called_once()
    mock_callbacks["direction"].assert_called_once_with(0, -1)


def test_input_system_with_no_adapter(world, mock_callbacks):
    """Test that InputSystem does nothing when no adapter is provided."""
    system = InputSystem(
        pygame_adapter=None,
        direction_callback=mock_callbacks["direction"],
    )

    # should not raise any errors
    system.update(world)

    mock_callbacks["direction"].assert_not_called()


def test_input_system_with_no_callbacks(world, mock_pygame_adapter):
    """Test that InputSystem handles events even without callbacks."""
    keydown_event = Mock()
    keydown_event.type = pygame.KEYDOWN
    keydown_event.key = pygame.K_p
    mock_pygame_adapter.get_events.return_value = [keydown_event]

    system = InputSystem(pygame_adapter=mock_pygame_adapter)

    # should not raise any errors
    system.update(world)


def test_input_system_prevents_180_degree_turns(
    world, mock_pygame_adapter, mock_callbacks
):
    """Test that InputSystem prevents 180-degree turns like the old code."""
    # test case: snake moving right (dx=1), player presses left (dx=-1)
    mock_callbacks["get_current_direction"].return_value = (1, 0)  # moving right

    keydown_event = Mock()
    keydown_event.type = pygame.KEYDOWN
    keydown_event.key = pygame.K_LEFT  # would be 180° turn
    mock_pygame_adapter.get_events.return_value = [keydown_event]

    system = InputSystem(
        pygame_adapter=mock_pygame_adapter,
        direction_callback=mock_callbacks["direction"],
        get_current_direction_callback=mock_callbacks["get_current_direction"],
    )

    system.update(world)

    # direction callback should NOT be called (180° turn prevented)
    mock_callbacks["direction"].assert_not_called()


def test_input_system_allows_valid_turns(world, mock_pygame_adapter, mock_callbacks):
    """Test that InputSystem allows valid direction changes."""
    # test case: snake moving right (dx=1), player presses up (dy=-1)
    mock_callbacks["get_current_direction"].return_value = (1, 0)  # moving right

    keydown_event = Mock()
    keydown_event.type = pygame.KEYDOWN
    keydown_event.key = pygame.K_UP  # valid turn
    mock_pygame_adapter.get_events.return_value = [keydown_event]

    system = InputSystem(
        pygame_adapter=mock_pygame_adapter,
        direction_callback=mock_callbacks["direction"],
        get_current_direction_callback=mock_callbacks["get_current_direction"],
    )

    system.update(world)

    # direction callback SHOULD be called (valid turn)
    mock_callbacks["direction"].assert_called_once_with(0, -1)


def test_input_system_allows_stopping(world, mock_pygame_adapter, mock_callbacks):
    """Test that InputSystem allows stopping (opposite direction when stopped)."""
    # test case: snake stopped (dx=0, dy=0), player presses any direction
    mock_callbacks["get_current_direction"].return_value = (0, 0)  # stopped

    keydown_event = Mock()
    keydown_event.type = pygame.KEYDOWN
    keydown_event.key = pygame.K_RIGHT
    mock_pygame_adapter.get_events.return_value = [keydown_event]

    system = InputSystem(
        pygame_adapter=mock_pygame_adapter,
        direction_callback=mock_callbacks["direction"],
        get_current_direction_callback=mock_callbacks["get_current_direction"],
    )

    system.update(world)

    # direction callback SHOULD be called (can start moving)
    mock_callbacks["direction"].assert_called_once_with(1, 0)
