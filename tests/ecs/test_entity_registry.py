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

    def test_new_registry_has_zero_id(self, registry):
        """Test that first entity gets ID 0."""
        snake = Snake(
            position=Position(0, 0),
            velocity=Velocity(),
            body=SnakeBody(),
            interpolation=Interpolation(),
        )
        entity_id = registry.add(snake)
        assert entity_id == 0


class TestAddingEntities:
    """Test adding entities to registry."""

    def test_add_entity_returns_id(self, registry, sample_snake):
        """Test that adding entity returns unique ID."""
        entity_id = registry.add(sample_snake)
        assert isinstance(entity_id, int)
        assert entity_id >= 0

    def test_add_multiple_entities_get_sequential_ids(
        self, registry, sample_snake, sample_apple, sample_obstacle
    ):
        """Test that entities get sequential IDs."""
        id1 = registry.add(sample_snake)
        id2 = registry.add(sample_apple)
        id3 = registry.add(sample_obstacle)

        assert id1 == 0
        assert id2 == 1
        assert id3 == 2

    def test_add_entity_increases_count(self, registry, sample_snake):
        """Test that adding entity increases count."""
        assert registry.count() == 0
        registry.add(sample_snake)
        assert registry.count() == 1

    def test_add_different_entity_types(
        self, registry, sample_snake, sample_apple, sample_obstacle
    ):
        """Test adding different types of entities."""
        snake_id = registry.add(sample_snake)
        apple_id = registry.add(sample_apple)
        obstacle_id = registry.add(sample_obstacle)

        assert registry.get(snake_id).get_type() == EntityType.SNAKE
        assert registry.get(apple_id).get_type() == EntityType.APPLE
        assert registry.get(obstacle_id).get_type() == EntityType.OBSTACLE


class TestGettingEntities:
    """Test retrieving entities from registry."""

    def test_get_returns_correct_entity(self, registry, sample_snake):
        """Test that get() returns the correct entity."""
        entity_id = registry.add(sample_snake)
        retrieved = registry.get(entity_id)
        assert retrieved is sample_snake

    def test_get_nonexistent_returns_none(self, registry):
        """Test that getting non-existent entity returns None."""
        assert registry.get(999) is None

    def test_get_after_adding_multiple(self, registry, sample_snake, sample_apple):
        """Test getting specific entities after adding multiple."""
        snake_id = registry.add(sample_snake)
        apple_id = registry.add(sample_apple)

        assert registry.get(snake_id) is sample_snake
        assert registry.get(apple_id) is sample_apple

    def test_has_returns_true_for_existing(self, registry, sample_snake):
        """Test that has() returns True for existing entity."""
        entity_id = registry.add(sample_snake)
        assert registry.has(entity_id) is True

    def test_has_returns_false_for_nonexistent(self, registry):
        """Test that has() returns False for non-existent entity."""
        assert registry.has(999) is False


class TestRemovingEntities:
    """Test removing entities from registry."""

    def test_remove_entity_decreases_count(self, registry, sample_snake):
        """Test that removing entity decreases count."""
        entity_id = registry.add(sample_snake)
        assert registry.count() == 1

        registry.remove(entity_id)
        assert registry.count() == 0

    def test_remove_entity_makes_it_unretrievable(self, registry, sample_snake):
        """Test that removed entity cannot be retrieved."""
        entity_id = registry.add(sample_snake)
        registry.remove(entity_id)

        assert registry.get(entity_id) is None
        assert registry.has(entity_id) is False

    def test_remove_nonexistent_entity_does_nothing(self, registry):
        """Test that removing non-existent entity doesn't error."""
        registry.remove(999)  # Should not raise error
        assert registry.count() == 0

    def test_remove_one_of_multiple_entities(
        self, registry, sample_snake, sample_apple, sample_obstacle
    ):
        """Test removing one entity from multiple."""
        snake_id = registry.add(sample_snake)
        apple_id = registry.add(sample_apple)
        obstacle_id = registry.add(sample_obstacle)

        registry.remove(apple_id)

        assert registry.count() == 2
        assert registry.get(snake_id) is sample_snake
        assert registry.get(apple_id) is None
        assert registry.get(obstacle_id) is sample_obstacle


class TestQueryByType:
    """Test querying entities by type."""

    def test_query_by_type_returns_empty_dict_when_none_found(self, registry):
        """Test that query returns empty dict when no matches."""
        result = registry.query_by_type(EntityType.SNAKE)
        assert result == {}

    def test_query_by_type_returns_matching_entities(self, registry, sample_snake):
        """Test that query returns entities of matching type."""
        entity_id = registry.add(sample_snake)

        snakes = registry.query_by_type(EntityType.SNAKE)

        assert len(snakes) == 1
        assert entity_id in snakes
        assert snakes[entity_id] is sample_snake

    def test_query_by_type_filters_out_other_types(
        self, registry, sample_snake, sample_apple, sample_obstacle
    ):
        """Test that query only returns specified type."""
        snake_id = registry.add(sample_snake)
        registry.add(sample_apple)
        registry.add(sample_obstacle)

        snakes = registry.query_by_type(EntityType.SNAKE)

        assert len(snakes) == 1
        assert snake_id in snakes

    def test_query_by_type_returns_multiple_matching(self, registry):
        """Test that query returns all entities of matching type."""
        snake1 = Snake(
            position=Position(0, 0),
            velocity=Velocity(),
            body=SnakeBody(),
            interpolation=Interpolation(),
        )
        snake2 = Snake(
            position=Position(100, 100),
            velocity=Velocity(),
            body=SnakeBody(),
            interpolation=Interpolation(),
        )

        id1 = registry.add(snake1)
        id2 = registry.add(snake2)

        snakes = registry.query_by_type(EntityType.SNAKE)

        assert len(snakes) == 2
        assert id1 in snakes
        assert id2 in snakes

    def test_count_by_type_returns_correct_count(
        self, registry, sample_snake, sample_apple
    ):
        """Test that count_by_type returns correct count."""
        registry.add(sample_snake)
        registry.add(sample_apple)
        registry.add(Apple(position=Position(50, 50), edible=Edible()))

        assert registry.count_by_type(EntityType.SNAKE) == 1
        assert registry.count_by_type(EntityType.APPLE) == 2
        assert registry.count_by_type(EntityType.OBSTACLE) == 0


class TestQueryByComponent:
    """Test querying entities by component."""

    def test_query_by_component_returns_entities_with_component(
        self, registry, sample_snake, sample_apple
    ):
        """Test that query returns entities with specified component."""
        snake_id = registry.add(sample_snake)
        apple_id = registry.add(sample_apple)

        # Both have position component
        result = registry.query_by_component("position")

        assert len(result) == 2
        assert snake_id in result
        assert apple_id in result

    def test_query_by_component_filters_by_component(
        self, registry, sample_snake, sample_apple
    ):
        """Test that query filters by component presence."""
        snake_id = registry.add(sample_snake)
        registry.add(sample_apple)

        # Only snake has velocity
        result = registry.query_by_component("velocity")

        assert len(result) == 1
        assert snake_id in result

    def test_query_by_multiple_components(
        self, registry, sample_snake, sample_apple, sample_obstacle
    ):
        """Test querying by multiple components (AND logic)."""
        snake_id = registry.add(sample_snake)
        registry.add(sample_apple)
        registry.add(sample_obstacle)

        # Only snake has both position and velocity
        result = registry.query_by_component("position", "velocity")

        assert len(result) == 1
        assert snake_id in result

    def test_query_by_nonexistent_component(self, registry, sample_snake):
        """Test querying for non-existent component returns empty."""
        registry.add(sample_snake)

        result = registry.query_by_component("nonexistent_component")

        assert len(result) == 0


class TestQueryByTypeAndComponents:
    """Test combined type and component queries."""

    def test_query_by_type_and_components_filters_both(self, registry):
        """Test that combined query filters by both type and components."""
        snake1 = Snake(
            position=Position(0, 0),
            velocity=Velocity(),
            body=SnakeBody(),
            interpolation=Interpolation(),
        )
        snake2 = Snake(
            position=Position(100, 100),
            velocity=Velocity(),
            body=SnakeBody(),
            interpolation=Interpolation(),
        )
        apple = Apple(position=Position(200, 200), edible=Edible())

        id1 = registry.add(snake1)
        id2 = registry.add(snake2)
        registry.add(apple)

        # Get snakes with interpolation
        result = registry.query_by_type_and_components(
            EntityType.SNAKE, "interpolation"
        )

        assert len(result) == 2
        assert id1 in result
        assert id2 in result

    def test_query_by_type_and_components_returns_empty_when_no_match(
        self, registry, sample_snake, sample_apple
    ):
        """Test that combined query returns empty when no matches."""
        registry.add(sample_snake)
        registry.add(sample_apple)

        # Apples don't have velocity
        result = registry.query_by_type_and_components(EntityType.APPLE, "velocity")

        assert len(result) == 0


class TestGetAll:
    """Test getting all entities."""

    def test_get_all_returns_all_entities(self, registry, sample_snake, sample_apple):
        """Test that get_all returns all entities."""
        id1 = registry.add(sample_snake)
        id2 = registry.add(sample_apple)

        all_entities = registry.get_all()

        assert len(all_entities) == 2
        assert id1 in all_entities
        assert id2 in all_entities

    def test_get_all_returns_copy(self, registry, sample_snake):
        """Test that get_all returns a copy, not reference."""
        registry.add(sample_snake)

        all_entities = registry.get_all()
        all_entities[999] = sample_snake  # Modify copy

        # Original registry should be unchanged
        assert registry.count() == 1
        assert not registry.has(999)

    def test_get_all_on_empty_registry(self, registry):
        """Test that get_all on empty registry returns empty dict."""
        assert registry.get_all() == {}


class TestClear:
    """Test clearing the registry."""

    def test_clear_removes_all_entities(
        self, registry, sample_snake, sample_apple, sample_obstacle
    ):
        """Test that clear removes all entities."""
        registry.add(sample_snake)
        registry.add(sample_apple)
        registry.add(sample_obstacle)

        assert registry.count() == 3

        registry.clear()

        assert registry.count() == 0
        assert registry.get_all() == {}

    def test_clear_resets_id_counter(self, registry, sample_snake):
        """Test that clear resets entity ID counter."""
        registry.add(sample_snake)
        registry.add(sample_snake)

        registry.clear()

        # Next entity should get ID 0
        new_id = registry.add(sample_snake)
        assert new_id == 0

    def test_clear_on_empty_registry(self, registry):
        """Test that clear on empty registry doesn't error."""
        registry.clear()  # Should not raise error
        assert registry.count() == 0


class TestEntityRegistryIntegration:
    """Integration tests for EntityRegistry."""

    def test_full_entity_lifecycle(self, registry, sample_snake, sample_apple):
        """Test complete lifecycle: add, query, modify, remove."""
        # Add entities
        snake_id = registry.add(sample_snake)
        apple_id = registry.add(sample_apple)

        # Query
        snakes = registry.query_by_type(EntityType.SNAKE)
        assert len(snakes) == 1

        # Modify entity
        snake = registry.get(snake_id)
        snake.position.x = 500

        # Verify modification persists
        retrieved_snake = registry.get(snake_id)
        assert retrieved_snake.position.x == 500

        # Remove
        registry.remove(apple_id)
        assert registry.count() == 1

    def test_multiple_operations_maintain_consistency(self, registry):
        """Test that multiple operations maintain registry consistency."""
        entities = []

        # Add 10 entities
        for i in range(10):
            snake = Snake(
                position=Position(i * 10, i * 10),
                velocity=Velocity(),
                body=SnakeBody(),
                interpolation=Interpolation(),
            )
            entity_id = registry.add(snake)
            entities.append(entity_id)

        assert registry.count() == 10

        # Remove every other entity
        for i in range(0, 10, 2):
            registry.remove(entities[i])

        assert registry.count() == 5

        # Verify remaining entities are correct
        for i in range(1, 10, 2):
            assert registry.has(entities[i])
