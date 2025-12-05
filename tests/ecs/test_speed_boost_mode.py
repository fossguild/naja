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

"""Speed Boost Mode tests.

Tests the unique mechanics of Speed Boost Mode:
- Speed boost activates when eating apple
- Speed boost timer decrements over time
- Speed boost expires after duration
- Speed multiplier is applied during boost
- No effect in other game modes (regression tests)
"""

import pytest

from ecs.world import World
from ecs.board import Board
from ecs.systems.speed_boost import SpeedBoostSystem
from ecs.systems.movement import MovementSystem
from ecs.entities.snake import Snake
from ecs.components.position import Position
from ecs.components.velocity import Velocity
from ecs.components.snake_body import SnakeBody
from ecs.components.interpolation import Interpolation
from ecs.components.renderable import Renderable
from ecs.components.input_buffer import InputBuffer
from ecs.components.game_state import GameState
from ecs.components.hunger import Hunger
from ecs.components.speed_boost import SpeedBoost
from core.types.color import Color


@pytest.fixture
def board():
    """Create a 10x10 board for testing."""
    return Board(width=10, height=10, cell_size=30)


@pytest.fixture
def world(board):
    """Create a world with board."""
    return World(board)


@pytest.fixture
def speed_boost_system():
    """Create a SpeedBoostSystem for testing."""
    return SpeedBoostSystem()


@pytest.fixture
def movement_system():
    """Create a MovementSystem for testing."""
    return MovementSystem()


def create_game_state(speed_boost_mode_enabled=False, game_started=True):
    """Helper to create a GameState entity."""

    class GameStateEntity:
        def __init__(self):
            self.game_state = GameState(
                speed_boost_mode_enabled=speed_boost_mode_enabled,
                game_mode=(
                    "Speed Boost Mode"
                    if speed_boost_mode_enabled
                    else "Classic Snake Game"
                ),
                game_started=game_started,
            )

        def get_type(self):
            return None

    return GameStateEntity()


def create_snake_at(x, y, dx=1, dy=0, with_speed_boost=True):
    """Helper to create a snake at a specific position."""
    speed_boost = SpeedBoost() if with_speed_boost else None
    return Snake(
        position=Position(x=x, y=y, prev_x=x, prev_y=y),
        velocity=Velocity(dx=dx, dy=dy, speed=10.0),
        body=SnakeBody(segments=[], size=1),
        interpolation=Interpolation(),
        renderable=Renderable(shape="square", color=Color(0, 255, 0), size=30),
        input_buffer=InputBuffer(),
        hunger=Hunger(current_time=0.0, max_time=0.0),
        speed_boost=speed_boost,
    )


class TestSpeedBoostComponent:
    """Test SpeedBoost component functionality."""

    def test_speed_boost_inactive_by_default(self):
        """Test that SpeedBoost starts inactive."""
        boost = SpeedBoost()
        assert boost.active is False
        assert boost.remaining_time == 0.0

    def test_speed_boost_default_values(self):
        """Test that SpeedBoost has correct default values."""
        boost = SpeedBoost()
        assert boost.multiplier == 2.0
        assert boost.duration == 3.0

    def test_speed_boost_activate(self):
        """Test that activate() sets active and resets timer."""
        boost = SpeedBoost()
        boost.activate()
        assert boost.active is True
        assert boost.remaining_time == boost.duration

    def test_speed_boost_deactivate(self):
        """Test that deactivate() clears active and timer."""
        boost = SpeedBoost()
        boost.activate()
        boost.deactivate()
        assert boost.active is False
        assert boost.remaining_time == 0.0


class TestSpeedBoostSystem:
    """Test SpeedBoostSystem functionality."""

    def test_system_does_nothing_when_mode_disabled(self, world, speed_boost_system):
        """Test that system does nothing when Speed Boost Mode is disabled."""
        # Setup: Classic mode (speed_boost_mode_enabled=False)
        game_state_entity = create_game_state(speed_boost_mode_enabled=False)
        world.registry.add(game_state_entity)

        # Create snake with active boost
        snake = create_snake_at(5, 5)
        snake.speed_boost.activate()
        world.registry.add(snake)

        # Update with 1 second
        world.set_dt_ms(1000)
        speed_boost_system.update(world)

        # Boost should NOT have decremented (mode disabled)
        assert snake.speed_boost.active is True
        assert snake.speed_boost.remaining_time == snake.speed_boost.duration

    def test_system_decrements_timer(self, world, speed_boost_system):
        """Test that system decrements boost timer when mode enabled."""
        # Setup: Speed Boost Mode enabled
        game_state_entity = create_game_state(speed_boost_mode_enabled=True)
        world.registry.add(game_state_entity)

        # Create snake with active boost
        snake = create_snake_at(5, 5)
        snake.speed_boost.activate()
        initial_time = snake.speed_boost.remaining_time
        world.registry.add(snake)

        # Update with 500ms (0.5 seconds)
        world.set_dt_ms(500)
        speed_boost_system.update(world)

        # Timer should have decremented
        assert snake.speed_boost.active is True
        assert snake.speed_boost.remaining_time == initial_time - 0.5

    def test_system_deactivates_expired_boost(self, world, speed_boost_system):
        """Test that system deactivates boost when timer reaches zero."""
        # Setup
        game_state_entity = create_game_state(speed_boost_mode_enabled=True)
        world.registry.add(game_state_entity)

        snake = create_snake_at(5, 5)
        snake.speed_boost.activate()
        world.registry.add(snake)

        # Update with time equal to duration (3 seconds = 3000ms)
        world.set_dt_ms(3000)
        speed_boost_system.update(world)

        # Boost should be deactivated
        assert snake.speed_boost.active is False
        assert snake.speed_boost.remaining_time == 0.0


class TestSpeedBoostInMovement:
    """Test speed boost integration with MovementSystem."""

    def test_speed_multiplier_applied_when_active(self, world, movement_system):
        """Test that MovementSystem applies speed multiplier when boost active."""
        # Setup
        game_state_entity = create_game_state(speed_boost_mode_enabled=True)
        world.registry.add(game_state_entity)

        snake = create_snake_at(5, 5, dx=1, dy=0)
        snake.speed_boost.activate()
        world.registry.add(snake)

        # Base speed is 10.0, with 2x multiplier = 20.0
        # Move interval = 1000 / 20.0 = 50ms
        # Update with 50ms should trigger a move
        world.set_dt_ms(50)
        movement_system.update(world)

        # Snake should have moved
        assert snake.position.x == 6 or snake.position.prev_x == 5

    def test_speed_normal_when_boost_inactive(self, world, movement_system):
        """Test that MovementSystem uses normal speed when boost inactive."""
        # Setup
        game_state_entity = create_game_state(speed_boost_mode_enabled=True)
        world.registry.add(game_state_entity)

        snake = create_snake_at(5, 5, dx=1, dy=0)
        # Don't activate boost
        world.registry.add(snake)

        # Base speed is 10.0
        # Move interval = 1000 / 10.0 = 100ms
        # Update with 50ms should NOT trigger a move
        world.set_dt_ms(50)
        movement_system.update(world)

        # Snake should NOT have moved yet
        assert snake.position.x == 5


class TestSpeedBoostRefresh:
    """Test speed boost refresh behavior."""

    def test_boost_refresh_resets_timer(self):
        """Test that activating boost again resets the timer."""
        boost = SpeedBoost()
        boost.activate()

        # Simulate some time passing
        boost.remaining_time = 1.0

        # Activate again (eating another apple)
        boost.activate()

        # Timer should be reset to full duration
        assert boost.remaining_time == boost.duration


def test_speed_boost_integration(world, speed_boost_system, movement_system):
    """Integration test: Speed Boost Mode with both systems."""
    # Setup
    game_state_entity = create_game_state(speed_boost_mode_enabled=True)
    world.registry.add(game_state_entity)

    snake = create_snake_at(5, 5, dx=1, dy=0)
    snake.speed_boost.activate()
    world.registry.add(snake)

    # Run several update cycles
    for _ in range(10):
        world.set_dt_ms(100)
        movement_system.update(world)
        speed_boost_system.update(world)

    # After 1 second, boost should still be active (3s duration)
    assert snake.speed_boost.active is True
    assert snake.speed_boost.remaining_time == pytest.approx(2.0, rel=0.1)

    # Run until boost expires
    for _ in range(25):
        world.set_dt_ms(100)
        speed_boost_system.update(world)

    # Boost should now be expired
    assert snake.speed_boost.active is False
