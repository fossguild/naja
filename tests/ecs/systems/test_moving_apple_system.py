#!/usr/bin/env python3
#
#   Copyright (c) 2023
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

"""Tests for the MovingAppleSystem."""

import pytest

from ecs.world import World
from ecs.board import Board
from ecs.systems.moving_apple import MovingAppleSystem
from ecs.components.game_state import GameState
from ecs.prefabs.snake import create_snake
from ecs.prefabs.apple import create_apple
from ecs.components.moving_apple import MovingApple


@pytest.fixture
def world():
    """Create a small square world for testing."""
    board = Board(width=6, height=6, cell_size=1)
    return World(board)


def _add_game_state(world: World, enabled: bool) -> GameState:
    """Attach a GameState entity to the world."""

    class GameStateEntity:
        def __init__(self, enabled: bool):
            self.game_state = GameState(
                moving_apples_enabled=enabled,
                game_mode="Moving Apple" if enabled else "Classic Snake Game",
            )

        def get_type(self):
            return None

    entity = GameStateEntity(enabled)
    world.registry.add(entity)
    return entity.game_state


def _add_snake(world: World) -> None:
    """Create a snake so the system can derive the current speed."""
    create_snake(world=world, grid_size=world.board.cell_size, initial_speed=5.0)


def test_apples_only_move_when_mode_enabled(world):
    """Verify that apples remain stationary unless the mode is active."""
    state = _add_game_state(world, enabled=False)
    _add_snake(world)

    apple_id = create_apple(world, x=2, y=2, grid_size=world.board.cell_size)
    system = MovingAppleSystem(
        base_speed_ratio=0.5,
        speed_ramp_rate=5.0,
        direction_change_chance=0.0,
        random_seed=123,
    )

    world.set_dt_ms(1000)
    system.update(world)
    apple = world.registry.get(apple_id)
    assert (apple.position.x, apple.position.y) == (2, 2)

    state.moving_apples_enabled = True
    world.set_dt_ms(1000)
    system.update(world)
    apple = world.registry.get(apple_id)
    assert (apple.position.x, apple.position.y) != (2, 2)


def test_apples_respect_board_boundaries(world):
    """Ensure apples pick a safe direction when the current one leaves the grid."""
    _add_game_state(world, enabled=True)
    _add_snake(world)

    edge_x = world.board.width - 1
    apple_id = create_apple(world, x=edge_x, y=3, grid_size=world.board.cell_size)
    apple = world.registry.get(apple_id)
    apple.moving_apple = MovingApple(dx=1, dy=0)  # would move out of bounds

    system = MovingAppleSystem(
        base_speed_ratio=0.5,
        speed_ramp_rate=5.0,
        direction_change_chance=0.0,
        random_seed=456,
    )
    world.set_dt_ms(1000)
    system.update(world)

    apple = world.registry.get(apple_id)
    assert 0 <= apple.position.x < world.board.width
    assert 0 <= apple.position.y < world.board.height
    # it should not have moved beyond the border
    assert apple.position.x <= edge_x
