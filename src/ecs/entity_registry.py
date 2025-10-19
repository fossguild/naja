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

"""Entity registry for managing game entities and querying them"""

from src.ecs.entities.entity import Entity, EntityType

__all__ = ["EntityRegistry"]


class EntityRegistry:
    """Registry for managing entities and their unique IDs.
    
    Handles entity storage, ID generation, and query operations.
    Supports both type-based and component-based queries.
    """

    _entities: dict[int, Entity]
    _next_entity_id: int

    def __init__(self) -> None:
        """Initialize empty entity registry."""
        self._entities = {}
        self._next_entity_id = 0

    def add(self, entity: Entity) -> int:
        """Add an entity to the registry.
        
        Args:
            entity: Entity to add (Snake, Apple, or Obstacle)
            
        Returns:
            int: Unique entity ID assigned to the entity
        """
        entity_id = self._next_entity_id
        self._next_entity_id += 1
        self._entities[entity_id] = entity
        return entity_id

    def get(self, entity_id: int) -> Entity | None:
        """Get an entity by ID.
        
        Args:
            entity_id: ID of entity to retrieve
            
        Returns:
            Entity or None if not found
        """
        return self._entities.get(entity_id)

    def remove(self, entity_id: int) -> None:
        """Remove an entity from the registry.
        
        Args:
            entity_id: ID of entity to remove
        """
        self._entities.pop(entity_id, None)

    def query_by_type(self, entity_type: EntityType) -> dict[int, Entity]:
        """Query all entities of a specific type.
        
        Args:
            entity_type: Type to filter by (SNAKE, APPLE, OBSTACLE)
            
        Returns:
            dict: Mapping of entity_id -> entity for matching type
            
        Example:
            snakes = registry.query_by_type(EntityType.SNAKE)
            for entity_id, snake in snakes.items():
                # Process snake
        """
        return {
            entity_id: entity
            for entity_id, entity in self._entities.items()
            if entity.get_type() == entity_type
        }

    def query_by_component(self, *component_names: str) -> dict[int, Entity]:
        """Query entities that have specific component fields.
        
        Args:
            *component_names: Component fields (as string names) to check for.
                              These correspond to the dataclass fields of the entity.
            
        Returns:
            dict: Mapping of entity_id -> entity matching criteria
            
        Example:
            # Get all entities with a 'position' component
            positioned_entities = registry.query_by_component("position")
            
            # Get all entities with 'position' and 'velocity' components
            moving_entities = registry.query_by_component("position", "velocity")
        """
        return {
            entity_id: entity
            for entity_id, entity in self._entities.items()
            if all(hasattr(entity, name) for name in component_names)
        }

    def query_by_type_and_components(
        self, entity_type: EntityType, *component_names: str
    ) -> dict[int, Entity]:
        """Query entities by both type and components.
        
        Args:
            entity_type: Type to filter by
            *component_names: Component fields to check for
            
        Returns:
            dict: Mapping of entity_id -> entity matching criteria
            
        Example:
            # Get all snakes with interpolation
            snakes = registry.query_by_type_and_components(
                EntityType.SNAKE, "interpolation"
            )
        """
        return {
            entity_id: entity
            for entity_id, entity in self._entities.items()
            if entity.get_type() == entity_type
            and all(hasattr(entity, name) for name in component_names)
        }

    def get_all(self) -> dict[int, Entity]:
        """Get all entities in the registry.
        
        Returns:
            dict: Mapping of entity_id -> entity
        """
        return self._entities.copy()

    def clear(self) -> None:
        """Remove all entities from the registry."""
        self._entities.clear()
        self._next_entity_id = 0

    def count(self) -> int:
        """Get total number of entities in the registry.
        
        Returns:
            int: Total entity count
        """
        return len(self._entities)

    def count_by_type(self, entity_type: EntityType) -> int:
        """Get count of entities of a specific type.
        
        Args:
            entity_type: Type to count
            
        Returns:
            int: Number of entities of that type
        """
        return sum(
            1 for entity in self._entities.values() if entity.get_type() == entity_type
        )

    def has(self, entity_id: int) -> bool:
        """Check if an entity ID exists in the registry.
        
        Args:
            entity_id: ID to check
            
        Returns:
            bool: True if entity exists, False otherwise
        """
        return entity_id in self._entities

