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

"""Spawn system for creating new entities in response to events.

This system handles spawning of apples at random free positions.
It ensures that spawned entities do not overlap with existing entities.
"""

from __future__ import annotations

import random
from typing import Optional

from src.ecs.systems.base_system import BaseSystem
from src.ecs.world import World
from src.ecs.entities.entity import EntityType
from src.ecs.entities.apple import Apple
from src.ecs.components.position import Position
from src.ecs.components.edible import Edible
from src.ecs.components.renderable import Renderable
from src.core.types.color import Color


class SpawnSystem(BaseSystem):
    """System for spawning new entities at valid positions.

    Reads: Position (all entities), Board (dimensions)
    Writes: New entities (Apple)
    Queries: entities with Position (to detect occupied cells)

    Responsibilities:
    - Spawn apples at random free positions
    - Verify spawn position is not occupied
    - Retry spawning with max attempts
    - Handle spawn requests from collision events
    - Prevent spawning when no free cells available

    Note: This system only CREATES entities in response to events.
    It does not directly modify existing entities.
    """

    def __init__(
        self,
        max_spawn_attempts: int = 1000,
        apple_color: tuple[int, int, int] = (255, 0, 0),
        random_seed: Optional[int] = None,
    ):
        """Initialize the SpawnSystem.

        Args:
            max_spawn_attempts: Maximum retry attempts for finding free cell
            apple_color: RGB color for spawned apples
            random_seed: Optional seed for deterministic spawning (testing)
        """
        self._max_spawn_attempts = max_spawn_attempts
        self._apple_color = apple_color
        if random_seed is not None:
            random.seed(random_seed)

    def update(self, world: World) -> None:
        """Check for spawn requests and create entities.

        This method is called every tick. It can be triggered by:
        - Collision events (apple eaten)
        - Initial game setup
        - Settings changes

        Args:
            world: ECS world containing entities and components
        """
        # stub implementation - will be connected to event system
        # when event handling is implemented in future issues

    def spawn_apple(self, world: World) -> Optional[int]:
        """Spawn a single apple at a valid free position.

        Args:
            world: ECS world to spawn apple in

        Returns:
            Entity ID of spawned apple, or None if no free cells available
        """
        # get board dimensions
        board = world.board
        grid_width = board.width
        grid_height = board.height
        grid_size = board.cell_size

        # get all occupied cells
        occupied_cells = self._get_occupied_cells(world)

        # calculate total cells
        total_cells = (grid_width // grid_size) * (grid_height // grid_size)

        # check if there are any free cells
        if len(occupied_cells) >= total_cells:
            return None  # no free cells available

        # try to find a free cell with retry logic
        for _ in range(self._max_spawn_attempts):
            # generate random position aligned to grid
            x = random.randrange(0, grid_width, grid_size)
            y = random.randrange(0, grid_height, grid_size)

            # check if this cell is free
            if (x, y) not in occupied_cells:
                # found a free cell, create apple entity
                return self._create_apple_entity(world, x, y, grid_size)

        # exhausted all attempts without finding free cell
        # this should be extremely rare unless board is almost full
        return None

    def spawn_multiple_apples(self, world: World, count: int) -> list[int]:
        """Spawn multiple apples at different valid positions.

        Args:
            world: ECS world to spawn apples in
            count: Number of apples to spawn

        Returns:
            List of entity IDs of spawned apples (may be less than count if not enough space)
        """
        spawned_ids = []

        for _ in range(count):
            apple_id = self.spawn_apple(world)
            if apple_id is not None:
                spawned_ids.append(apple_id)
            else:
                # no more free cells, stop spawning
                break

        return spawned_ids

    def get_free_cells_count(self, world: World) -> int:
        """Calculate number of free (unoccupied) cells in the grid.

        Args:
            world: ECS world to analyze

        Returns:
            Number of free cells
        """
        board = world.board
        grid_size = board.cell_size

        # calculate total cells
        total_cells = (board.width // grid_size) * (board.height // grid_size)

        # get occupied cells count
        occupied_count = len(self._get_occupied_cells(world))

        return total_cells - occupied_count

    def _get_occupied_cells(self, world: World) -> set[tuple[int, int]]:
        """Get set of all occupied cell positions.

        Args:
            world: ECS world to query

        Returns:
            Set of (x, y) tuples representing occupied cells
        """
        occupied = set()
        registry = world.registry

        # collect all entities with position component
        for entity_id in registry.query_by_component("position"):
            entity = registry.get(entity_id)
            if entity and hasattr(entity, "position"):
                pos = entity.position
                occupied.add((pos.x, pos.y))

        # also include snake body segments if snake has body component
        snakes = registry.query_by_type(EntityType.SNAKE)
        for _snake_id, snake in snakes.items():
            if hasattr(snake, "body") and hasattr(snake.body, "segments"):
                for segment in snake.body.segments:
                    occupied.add((segment.x, segment.y))

        return occupied

    def _create_apple_entity(self, world: World, x: int, y: int, grid_size: int) -> int:
        """Create a new apple entity at specified position.

        Args:
            world: ECS world to create entity in
            x: X position (grid-aligned)
            y: Y position (grid-aligned)
            grid_size: Size of grid cell (for renderable size)

        Returns:
            Entity ID of created apple
        """
        # create apple entity with required components
        apple = Apple(
            position=Position(x=x, y=y),
            edible=Edible(points=10, growth=1),
            renderable=Renderable(
                shape="circle",
                color=Color(
                    self._apple_color[0], self._apple_color[1], self._apple_color[2]
                ),
                size=grid_size,
            ),
        )

        # register entity with world
        entity_id = world.registry.add(apple)

        return entity_id
