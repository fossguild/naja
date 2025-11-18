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

"""Tests for CollisionSystem."""

import pytest
from unittest.mock import Mock

from ecs.systems.collision import CollisionSystem
from ecs.world import World
from ecs.board import Board


@pytest.fixture
def world():
    """Create a test world."""
    board = Board(20, 20)
    return World(board)


@pytest.fixture
def mock_callbacks():
    """Create mock callback functions."""
    return {
        "get_snake_head_position": Mock(return_value=(100, 100)),
        "get_snake_tail_positions": Mock(return_value=[]),
        "get_snake_next_position": Mock(return_value=(120, 100)),
        "get_electric_walls": Mock(return_value=True),
        "get_grid_dimensions": Mock(return_value=(800, 600, 20)),
        "get_current_speed": Mock(return_value=5.0),
        "get_max_speed": Mock(return_value=20.0),
        "death": Mock(),
        "apple_eaten": Mock(),
        "speed_increase": Mock(),
    }


def test_collision_system_with_no_callbacks(world):
    """Test that CollisionSystem handles missing callbacks gracefully."""
    system = CollisionSystem()

    # should not raise any errors
    system.update(world)
