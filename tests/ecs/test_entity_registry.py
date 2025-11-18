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

"""EntityRegistry class tests."""

import pytest
from ecs.entity_registry import EntityRegistry
from ecs.entities import Snake, Apple, Obstacle, EntityType
from ecs.components import (
    Position,
    Velocity,
    SnakeBody,
    Interpolation,
    Edible,
    ObstacleTag,
    InputBuffer,
)


@pytest.fixture
def registry():
    """Create a fresh EntityRegistry for each test."""
    return EntityRegistry()


@pytest.fixture
def sample_snake():
    """Create a sample snake entity."""
    return Snake(
        position=Position(100, 100),
        velocity=Velocity(1, 0, 10.0),
        body=SnakeBody(),
        interpolation=Interpolation(),
        input_buffer=InputBuffer(),
    )


@pytest.fixture
def sample_apple():
    """Create a sample apple entity."""
    return Apple(position=Position(200, 200), edible=Edible(points=10, growth=1))


@pytest.fixture
def sample_obstacle():
    """Create a sample obstacle entity."""
    return Obstacle(position=Position(300, 300), tag=ObstacleTag())


class TestEntityRegistryInitialization:
    """Test entity registry initialization."""

    def test_new_registry_is_empty(self, registry):
        """Test that a new registry starts empty."""
        assert registry.count() == 0
        assert registry.get_all() == {}


class TestAddingEntities:
    """Test adding entities to registry."""


class TestGettingEntities:
    """Test retrieving entities from registry."""

    def test_get_nonexistent_returns_none(self, registry):
        """Test that getting non-existent entity returns None."""
        assert registry.get(999) is None

    def test_has_returns_false_for_nonexistent(self, registry):
        """Test that has() returns False for non-existent entity."""
        assert registry.has(999) is False


class TestQueryByType:
    """Test querying entities by type."""

    def test_query_by_type_returns_empty_dict_when_none_found(self, registry):
        """Test that query returns empty dict when no matches."""
        result = registry.query_by_type(EntityType.SNAKE)
        assert result == {}


class TestGetAll:
    """Test getting all entities."""

    def test_get_all_on_empty_registry(self, registry):
        """Test that get_all on empty registry returns empty dict."""
        assert registry.get_all() == {}


class TestClear:
    """Test clearing the registry."""

    def test_clear_on_empty_registry(self, registry):
        """Test that clear on empty registry doesn't error."""
        registry.clear()  # Should not raise error
        assert registry.count() == 0
