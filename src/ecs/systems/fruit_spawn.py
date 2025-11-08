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

"""Multi-fruit spawn system for More Fruits game mode.

This system spawns different fruit types with weighted probabilities:
- Apple (Red): 65% spawn rate, +1 segment, speed up
- Grape (Purple): 25% spawn rate, +1 segment, slow down
- Orange: 10% spawn rate, +2 segments, speed up
"""

from __future__ import annotations

import random
from typing import Optional

from src.ecs.systems.base_system import BaseSystem
from src.ecs.world import World
from src.ecs.entities.entity import EntityType
from src.ecs.prefabs.apple import create_apple
from src.ecs.prefabs.grape import create_grape
from src.ecs.prefabs.orange import create_orange


class FruitSpawnSystem(BaseSystem):
    """System for spawning multiple fruit types with weighted probabilities.

    Reads: AppleConfig (desired count), Apple entities (current count)
    Writes: Creates new fruit entities (apple, grape, orange) as needed

    Responsibilities:
    - Count current number of fruits in the world
    - Spawn new fruits if count is below desired
    - Use weighted random selection for fruit type
    - Find valid spawn positions (avoiding snake, obstacles, other fruits)

    Spawn Probabilities:
    - Apple: 65% (0.00 - 0.65)
    - Grape: 25% (0.65 - 0.90)
    - Orange: 10% (0.90 - 1.00)
    """

    def __init__(self, max_spawn_attempts: int = 1000):
        """Initialize the FruitSpawnSystem.

        Args:
            max_spawn_attempts: Maximum attempts to find a valid spawn position
        """
        self._max_spawn_attempts = max_spawn_attempts

    def update(self, world: World) -> None:
        """Check fruit count and spawn new fruits if needed.

        Args:
            world: ECS world containing entities and components
        """
        # get desired fruit count from config
        desired_count = self._get_desired_fruit_count(world)

        if desired_count <= 0:
            return

        # count current fruits (apples represent all fruit types)
        current_fruits = world.registry.query_by_type(EntityType.APPLE)
        current_count = len(current_fruits)

        # spawn new fruits if we're below desired count
        fruits_to_spawn = desired_count - current_count

        if fruits_to_spawn > 0:
            grid_size = world.board.cell_size

            for _ in range(fruits_to_spawn):
                position = self._find_valid_position(world)
                if position:
                    x, y = position
                    self._spawn_random_fruit(world, x, y, grid_size)

    def _spawn_random_fruit(self, world: World, x: int, y: int, grid_size: int) -> None:
        """Spawn a random fruit type based on weighted probabilities.

        Probabilities:
        - Apple: 65% (0.00 - 0.65)
        - Grape: 25% (0.65 - 0.90)
        - Orange: 10% (0.90 - 1.00)

        Args:
            world: ECS world
            x: X position in grid coordinates
            y: Y position in grid coordinates
            grid_size: Size of each grid cell
        """
        rand = random.random()

        if rand < 0.65:
            # apple - 65% chance
            create_apple(world, x=x, y=y, grid_size=grid_size, color=None)
        elif rand < 0.90:
            # grape - 25% chance
            create_grape(world, x=x, y=y, grid_size=grid_size, color=None)
        else:
            # orange - 10% chance
            create_orange(world, x=x, y=y, grid_size=grid_size, color=None)

    def _get_desired_fruit_count(self, world: World) -> int:
        """Get the desired number of fruits from AppleConfig component.

        Args:
            world: ECS world

        Returns:
            Desired fruit count, or 1 if no config found
        """
        # query for entities with AppleConfig component
        config_entities = world.registry.query_by_component("apple_config")

        if config_entities:
            config_entity = list(config_entities.values())[0]
            if hasattr(config_entity, "apple_config"):
                return config_entity.apple_config.desired_count

        return 1  # default to 1 fruit

    def _find_valid_position(self, world: World) -> Optional[tuple[int, int]]:
        """Find a valid position to spawn a fruit.

        A valid position is one that:
        - Is within board bounds
        - Doesn't overlap with snake head
        - Doesn't overlap with snake body segments
        - Doesn't overlap with obstacles
        - Doesn't overlap with existing fruits

        Args:
            world: ECS world

        Returns:
            (x, y) tuple if valid position found, None otherwise
        """
        board = world.board

        # get occupied positions
        occupied = self._get_occupied_positions(world)

        # try to find a valid position
        for _ in range(self._max_spawn_attempts):
            x = random.randint(0, board.width - 1)
            y = random.randint(0, board.height - 1)

            if (x, y) not in occupied:
                return (x, y)

        # if we couldn't find a position after max attempts, return None
        return None

    def _get_occupied_positions(self, world: World) -> set[tuple[int, int]]:
        """Get all positions currently occupied by game entities.

        Args:
            world: ECS world

        Returns:
            Set of (x, y) tuples representing occupied positions
        """
        occupied = set()

        # get snake positions
        snakes = world.registry.query_by_type(EntityType.SNAKE)
        for _, snake in snakes.items():
            if hasattr(snake, "position"):
                # add head position
                occupied.add((snake.position.x, snake.position.y))

                # add body segments
                if hasattr(snake, "body"):
                    for segment in snake.body.segments:
                        occupied.add((segment.x, segment.y))

        # get obstacle positions
        obstacles = world.registry.query_by_type(EntityType.OBSTACLE)
        for _, obstacle in obstacles.items():
            if hasattr(obstacle, "position"):
                occupied.add((obstacle.position.x, obstacle.position.y))

        # get existing fruit positions (all apples are fruits)
        fruits = world.registry.query_by_type(EntityType.APPLE)
        for _, fruit in fruits.items():
            if hasattr(fruit, "position"):
                occupied.add((fruit.position.x, fruit.position.y))

        return occupied
