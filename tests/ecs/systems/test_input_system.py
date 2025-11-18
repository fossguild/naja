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

from ecs.systems.input import InputSystem
from ecs.world import World
from ecs.board import Board


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


def test_input_system_with_no_callbacks(world, mock_pygame_adapter):
    """Test that InputSystem handles events even without callbacks."""
    keydown_event = Mock()
    keydown_event.type = pygame.KEYDOWN
    keydown_event.key = pygame.K_p
    mock_pygame_adapter.get_events.return_value = [keydown_event]

    system = InputSystem(pygame_adapter=mock_pygame_adapter)

    # should not raise any errors
    system.update(world)
