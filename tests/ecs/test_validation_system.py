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

"""Validation system tests."""

import pytest
import logging
from dataclasses import dataclass, field
from typing import List
from unittest.mock import patch

from src.ecs.world import World
from src.ecs.board import Board
from src.ecs.systems.validation import ValidationSystem
from src.ecs.entities.entity import EntityType


@dataclass
class Position:
    """Simple position component for testing."""

    x: int
    y: int


@dataclass
class Edible:
    """Simple edible component for testing."""

    points: int = 10
    growth: int = 1


@dataclass
class ObstacleTag:
    """Simple obstacle tag for testing."""

    pass


@dataclass
class SnakeBody:
    """Simple snake body component for testing."""

    segments: List[Position] = field(default_factory=list)


@dataclass
class AppleEntity:
    """Simple apple entity for testing."""

    position: Position
    edible: Edible
    entity_type: EntityType = EntityType.APPLE


@dataclass
class SnakeEntity:
    """Simple snake entity for testing."""

    position: Position
    body: SnakeBody
    entity_type: EntityType = EntityType.SNAKE


@dataclass
class ObstacleEntity:
    """Simple obstacle entity for testing."""

    position: Position
    tag: ObstacleTag
    entity_type: EntityType = EntityType.OBSTACLE


@pytest.fixture
def board():
    """Create a standard board for testing."""
    return Board(width=600, height=400, cell_size=20)


@pytest.fixture
def world(board):
    """Create a world with board."""
    return World(board)


@pytest.fixture
def validation_system():
    """Create a ValidationSystem."""
    return ValidationSystem(
        enabled=True, expected_apple_count=1, log_level=logging.WARNING
    )


@pytest.fixture
def validation_system_disabled():
    """Create a disabled ValidationSystem."""
    return ValidationSystem(enabled=False, expected_apple_count=1)


class TestValidationSystemInitialization:
    """Test ValidationSystem initialization."""

    def test_system_created_successfully(self):
        """Test that ValidationSystem can be initialized."""
        system = ValidationSystem()
        assert system is not None

    def test_system_enabled_by_default(self):
        """Test system is enabled by default."""
        system = ValidationSystem()
        assert system.is_enabled() is True

    def test_system_can_be_disabled(self):
        """Test system can be created disabled."""
        system = ValidationSystem(enabled=False)
        assert system.is_enabled() is False

    def test_expected_apple_count_configurable(self):
        """Test expected apple count can be configured."""
        system = ValidationSystem(expected_apple_count=3)
        assert system.get_expected_apple_count() == 3

    def test_statistics_start_at_zero(self, validation_system):
        """Test validation statistics start at zero."""
        assert validation_system.get_validation_count() == 0
        assert validation_system.get_anomaly_count() == 0


class TestAppleCountValidation:
    """Test apple count validation."""

    def test_validate_apple_count_correct(self, world, validation_system):
        """Test validation passes with correct apple count."""
        # add exactly one apple
        apple = AppleEntity(position=Position(100, 100), edible=Edible())
        world.registry.add(apple)

        result = validation_system.validate_apple_count(world)
        assert result is True

    def test_validate_apple_count_zero_apples(self, world, validation_system):
        """Test validation fails with zero apples."""
        # no apples added
        result = validation_system.validate_apple_count(world)
        assert result is False

    def test_validate_apple_count_too_many(self, world, validation_system):
        """Test validation fails with too many apples."""
        # add two apples (expected: 1)
        apple1 = AppleEntity(position=Position(100, 100), edible=Edible())
        apple2 = AppleEntity(position=Position(200, 200), edible=Edible())
        world.registry.add(apple1)
        world.registry.add(apple2)

        result = validation_system.validate_apple_count(world)
        assert result is False

    def test_validate_apple_count_multiple_expected(self, world):
        """Test validation with multiple apples expected."""
        system = ValidationSystem(expected_apple_count=3)

        # add exactly 3 apples
        for i in range(3):
            apple = AppleEntity(position=Position(100 * i, 100), edible=Edible())
            world.registry.add(apple)

        result = system.validate_apple_count(world)
        assert result is True


class TestSnakeBoundsValidation:
    """Test snake position bounds validation."""

    def test_validate_snake_in_bounds(self, world, validation_system):
        """Test validation passes when snake is in bounds."""
        # board is 600x400
        snake = SnakeEntity(
            position=Position(300, 200),  # center of board
            body=SnakeBody(segments=[Position(280, 200), Position(260, 200)]),
        )
        world.registry.add(snake)

        result = validation_system.validate_snake_bounds(world)
        assert result is True

    def test_validate_snake_head_out_of_bounds_x(self, world, validation_system):
        """Test validation fails when snake head X is out of bounds."""
        # board width is 600
        snake = SnakeEntity(
            position=Position(700, 200),  # X out of bounds
            body=SnakeBody(),
        )
        world.registry.add(snake)

        result = validation_system.validate_snake_bounds(world)
        assert result is False

    def test_validate_snake_head_out_of_bounds_y(self, world, validation_system):
        """Test validation fails when snake head Y is out of bounds."""
        # board height is 400
        snake = SnakeEntity(
            position=Position(300, 500),  # Y out of bounds
            body=SnakeBody(),
        )
        world.registry.add(snake)

        result = validation_system.validate_snake_bounds(world)
        assert result is False

    def test_validate_snake_head_negative_position(self, world, validation_system):
        """Test validation fails with negative position."""
        snake = SnakeEntity(
            position=Position(-10, -20),  # negative coordinates
            body=SnakeBody(),
        )
        world.registry.add(snake)

        result = validation_system.validate_snake_bounds(world)
        assert result is False

    def test_validate_snake_body_out_of_bounds(self, world, validation_system):
        """Test validation fails when body segment is out of bounds."""
        snake = SnakeEntity(
            position=Position(300, 200),  # head in bounds
            body=SnakeBody(
                segments=[
                    Position(280, 200),  # in bounds
                    Position(700, 200),  # out of bounds
                ]
            ),
        )
        world.registry.add(snake)

        result = validation_system.validate_snake_bounds(world)
        assert result is False

    def test_validate_multiple_snakes(self, world, validation_system):
        """Test validation with multiple snakes."""
        snake1 = SnakeEntity(position=Position(100, 100), body=SnakeBody())
        snake2 = SnakeEntity(position=Position(200, 200), body=SnakeBody())
        world.registry.add(snake1)
        world.registry.add(snake2)

        result = validation_system.validate_snake_bounds(world)
        assert result is True


class TestEntityOverlapValidation:
    """Test entity overlap validation."""

    def test_validate_no_overlaps(self, world, validation_system):
        """Test validation passes with no overlaps."""
        # add entities at different positions
        apple = AppleEntity(position=Position(100, 100), edible=Edible())
        snake = SnakeEntity(position=Position(200, 200), body=SnakeBody())
        obstacle = ObstacleEntity(position=Position(300, 300), tag=ObstacleTag())

        world.registry.add(apple)
        world.registry.add(snake)
        world.registry.add(obstacle)

        result = validation_system.validate_entity_overlaps(world)
        assert result is True

    def test_validate_snake_on_obstacle(self, world, validation_system):
        """Test validation fails when snake head is on obstacle."""
        # snake and obstacle at same position
        snake = SnakeEntity(position=Position(100, 100), body=SnakeBody())
        obstacle = ObstacleEntity(position=Position(100, 100), tag=ObstacleTag())

        world.registry.add(snake)
        world.registry.add(obstacle)

        result = validation_system.validate_entity_overlaps(world)
        assert result is False

    def test_validate_snake_body_on_obstacle(self, world, validation_system):
        """Test validation fails when snake body is on obstacle."""
        snake = SnakeEntity(
            position=Position(100, 100),
            body=SnakeBody(segments=[Position(120, 100)]),
        )
        obstacle = ObstacleEntity(position=Position(120, 100), tag=ObstacleTag())

        world.registry.add(snake)
        world.registry.add(obstacle)

        result = validation_system.validate_entity_overlaps(world)
        assert result is False

    def test_validate_multiple_entities_same_position(self, world, validation_system):
        """Test validation flags multiple entities at same position."""
        # three entities at same position (suspicious)
        apple1 = AppleEntity(position=Position(100, 100), edible=Edible())
        apple2 = AppleEntity(position=Position(100, 100), edible=Edible())
        apple3 = AppleEntity(position=Position(100, 100), edible=Edible())

        world.registry.add(apple1)
        world.registry.add(apple2)
        world.registry.add(apple3)

        result = validation_system.validate_entity_overlaps(world)
        assert result is False


class TestValidateAll:
    """Test validate_all method."""

    def test_validate_all_passes(self, world, validation_system):
        """Test validate_all with valid game state."""
        # valid state: 1 apple, snake in bounds, no overlaps
        apple = AppleEntity(position=Position(100, 100), edible=Edible())
        snake = SnakeEntity(position=Position(200, 200), body=SnakeBody())

        world.registry.add(apple)
        world.registry.add(snake)

        result = validation_system.validate_all(world)
        assert result is True

    def test_validate_all_fails_apple_count(self, world, validation_system):
        """Test validate_all fails with wrong apple count."""
        # no apples, but one expected
        snake = SnakeEntity(position=Position(200, 200), body=SnakeBody())
        world.registry.add(snake)

        result = validation_system.validate_all(world)
        assert result is False

    def test_validate_all_fails_bounds(self, world, validation_system):
        """Test validate_all fails with out of bounds snake."""
        apple = AppleEntity(position=Position(100, 100), edible=Edible())
        snake = SnakeEntity(
            position=Position(700, 500),  # out of bounds
            body=SnakeBody(),
        )

        world.registry.add(apple)
        world.registry.add(snake)

        result = validation_system.validate_all(world)
        assert result is False

    def test_validate_all_fails_overlaps(self, world, validation_system):
        """Test validate_all fails with invalid overlaps."""
        apple = AppleEntity(position=Position(100, 100), edible=Edible())
        snake = SnakeEntity(position=Position(200, 200), body=SnakeBody())
        obstacle = ObstacleEntity(position=Position(200, 200), tag=ObstacleTag())

        world.registry.add(apple)
        world.registry.add(snake)
        world.registry.add(obstacle)

        result = validation_system.validate_all(world)
        assert result is False


class TestEnableDisable:
    """Test enable/disable functionality."""

    def test_set_enabled(self, validation_system):
        """Test enabling/disabling validation."""
        validation_system.set_enabled(False)
        assert validation_system.is_enabled() is False

        validation_system.set_enabled(True)
        assert validation_system.is_enabled() is True

    def test_update_skips_when_disabled(self, world, validation_system_disabled):
        """Test update does nothing when disabled."""
        # create invalid state (no apples)
        snake = SnakeEntity(position=Position(200, 200), body=SnakeBody())
        world.registry.add(snake)

        # update should not increment validation count
        validation_system_disabled.update(world)

        assert validation_system_disabled.get_validation_count() == 0
        assert validation_system_disabled.get_anomaly_count() == 0

    def test_update_runs_when_enabled(self, world, validation_system):
        """Test update runs validations when enabled."""
        # valid state
        apple = AppleEntity(position=Position(100, 100), edible=Edible())
        world.registry.add(apple)

        validation_system.update(world)

        assert validation_system.get_validation_count() == 1
        assert validation_system.get_anomaly_count() == 0


class TestExpectedAppleCount:
    """Test expected apple count configuration."""

    def test_set_expected_apple_count(self, validation_system):
        """Test changing expected apple count."""
        validation_system.set_expected_apple_count(5)
        assert validation_system.get_expected_apple_count() == 5

    def test_validation_respects_updated_count(self, world):
        """Test validation uses updated apple count."""
        system = ValidationSystem(expected_apple_count=1)

        # add 3 apples
        for i in range(3):
            apple = AppleEntity(position=Position(100 * i, 100), edible=Edible())
            world.registry.add(apple)

        # should fail with expected count = 1
        assert system.validate_apple_count(world) is False

        # update expected count to 3
        system.set_expected_apple_count(3)

        # should now pass
        assert system.validate_apple_count(world) is True


class TestStatistics:
    """Test validation statistics tracking."""

    def test_validation_count_increments(self, world, validation_system):
        """Test validation count increments on each update."""
        apple = AppleEntity(position=Position(100, 100), edible=Edible())
        world.registry.add(apple)

        validation_system.update(world)
        assert validation_system.get_validation_count() == 1

        validation_system.update(world)
        assert validation_system.get_validation_count() == 2

        validation_system.update(world)
        assert validation_system.get_validation_count() == 3

    def test_anomaly_count_tracks_failures(self, world, validation_system):
        """Test anomaly count tracks validation failures."""
        # invalid state: no apples
        snake = SnakeEntity(position=Position(200, 200), body=SnakeBody())
        world.registry.add(snake)

        # run multiple validations with anomalies
        validation_system.update(world)
        validation_system.update(world)

        assert validation_system.get_validation_count() == 2
        assert validation_system.get_anomaly_count() == 2

    def test_anomaly_count_only_increments_with_failures(
        self, world, validation_system
    ):
        """Test anomaly count only increments on failures."""
        apple = AppleEntity(position=Position(100, 100), edible=Edible())
        world.registry.add(apple)

        # first update: valid state
        validation_system.update(world)
        assert validation_system.get_validation_count() == 1
        assert validation_system.get_anomaly_count() == 0

        # remove apple to create invalid state
        world.registry.remove(1)

        # second update: invalid state
        validation_system.update(world)
        assert validation_system.get_validation_count() == 2
        assert validation_system.get_anomaly_count() == 1

    def test_reset_statistics(self, world, validation_system):
        """Test resetting statistics."""
        apple = AppleEntity(position=Position(100, 100), edible=Edible())
        world.registry.add(apple)

        validation_system.update(world)
        validation_system.update(world)

        assert validation_system.get_validation_count() == 2

        validation_system.reset_statistics()

        assert validation_system.get_validation_count() == 0
        assert validation_system.get_anomaly_count() == 0

    def test_get_statistics_dict(self, world, validation_system):
        """Test getting statistics as dictionary."""
        apple = AppleEntity(position=Position(100, 100), edible=Edible())
        world.registry.add(apple)

        validation_system.update(world)

        stats = validation_system.get_statistics()

        assert isinstance(stats, dict)
        assert "validation_count" in stats
        assert "anomaly_count" in stats
        assert stats["validation_count"] == 1
        assert stats["anomaly_count"] == 0


@patch("src.ecs.systems.validation.logger")
class TestLogging:
    """Test logging functionality."""

    def test_logs_warning_for_apple_count(self, mock_logger, world, validation_system):
        """Test warning is logged for wrong apple count."""
        # no apples (expected: 1)
        validation_system.validate_apple_count(world)

        mock_logger.warning.assert_called()
        call_args = str(mock_logger.warning.call_args)
        assert "apple count" in call_args.lower()

    def test_logs_warning_for_out_of_bounds(
        self, mock_logger, world, validation_system
    ):
        """Test warning is logged for out of bounds snake."""
        snake = SnakeEntity(position=Position(700, 500), body=SnakeBody())
        world.registry.add(snake)

        validation_system.validate_snake_bounds(world)

        mock_logger.warning.assert_called()
        call_args = str(mock_logger.warning.call_args)
        assert "out of bounds" in call_args.lower()

    def test_logs_warning_for_overlaps(self, mock_logger, world, validation_system):
        """Test warning is logged for invalid overlaps."""
        snake = SnakeEntity(position=Position(100, 100), body=SnakeBody())
        obstacle = ObstacleEntity(position=Position(100, 100), tag=ObstacleTag())
        world.registry.add(snake)
        world.registry.add(obstacle)

        validation_system.validate_entity_overlaps(world)

        mock_logger.warning.assert_called()
        call_args = str(mock_logger.warning.call_args)
        assert "overlap" in call_args.lower()


class TestIntegration:
    """Integration tests for ValidationSystem."""

    def test_full_validation_cycle(self, world, validation_system):
        """Test complete validation workflow."""
        # start with valid state
        apple = AppleEntity(position=Position(100, 100), edible=Edible())
        snake = SnakeEntity(position=Position(200, 200), body=SnakeBody())
        world.registry.add(apple)
        world.registry.add(snake)

        # first validation: should pass
        validation_system.update(world)
        assert validation_system.get_validation_count() == 1
        assert validation_system.get_anomaly_count() == 0

        # second validation: should still pass
        validation_system.update(world)
        assert validation_system.get_validation_count() == 2
        assert validation_system.get_anomaly_count() == 0

        # introduce anomaly: move snake out of bounds
        snake.position.x = 700
        snake.position.y = 500

        # third validation: should detect anomaly
        validation_system.update(world)
        assert validation_system.get_validation_count() == 3
        assert validation_system.get_anomaly_count() == 1

        # fix anomaly
        snake.position.x = 200
        snake.position.y = 200

        # fourth validation: should pass again
        validation_system.update(world)
        assert validation_system.get_validation_count() == 4
        assert validation_system.get_anomaly_count() == 1  # count doesn't decrease

    def test_validation_with_complex_game_state(self, world):
        """Test validation with complex game state."""
        system = ValidationSystem(expected_apple_count=2)

        # add multiple entities
        apple1 = AppleEntity(position=Position(100, 100), edible=Edible())
        apple2 = AppleEntity(position=Position(300, 300), edible=Edible())
        snake = SnakeEntity(
            position=Position(200, 200),
            body=SnakeBody(
                segments=[
                    Position(180, 200),
                    Position(160, 200),
                    Position(140, 200),
                ]
            ),
        )
        obstacle1 = ObstacleEntity(position=Position(400, 100), tag=ObstacleTag())
        obstacle2 = ObstacleEntity(position=Position(500, 100), tag=ObstacleTag())

        world.registry.add(apple1)
        world.registry.add(apple2)
        world.registry.add(snake)
        world.registry.add(obstacle1)
        world.registry.add(obstacle2)

        # all validations should pass
        assert system.validate_all(world) is True
