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

"""Poisoned apple spawn system for Poisoned Apple game mode.

This system maintains:
- 1 regular apple (red) - always present, safe to eat
- 0-1 poisoned apple (dark purple) - occasionally spawns, deadly!

The poisoned apple spawns randomly with configurable probability.
When a new poisoned apple spawns, the old one is removed.
"""

from __future__ import annotations

import random
from typing import Optional

from src.ecs.systems.base_system import BaseSystem
from src.ecs.world import World
from src.ecs.entities.entity import EntityType
from src.ecs.prefabs.apple import create_apple
from src.ecs.prefabs.poisoned_apple import create_poisoned_apple


class PoisonedAppleSpawnSystem(BaseSystem):
    """System for spawning regular and poisoned apples.

    Reads: AppleConfig (desired count), Apple entities (current count)
    Writes: Creates new apple entities (regular or poisoned) as needed

    Responsibilities:
    - Maintain exactly 1 regular apple on the board
    - Occasionally spawn 1 poisoned apple (based on probability)
    - Remove old poisoned apple when spawning a new one
    - Find valid spawn positions (avoiding snake, obstacles, other apples)

    Strategy:
    - Regular apple is always present (player can always progress)
    - Poisoned apple spawns with configurable probability per update
    - Only 1 poisoned apple exists at a time
    """

    def __init__(
        self,
        max_spawn_attempts: int = 1000,
        poison_spawn_chance: float = 0.01,
    ):
        """Initialize the PoisonedAppleSpawnSystem.

        Args:
            max_spawn_attempts: Maximum attempts to find a valid spawn position
            poison_spawn_chance: Probability per update of spawning poisoned apple
                                 (default 0.01 = 1% chance per frame)
        """
        self._max_spawn_attempts = max_spawn_attempts
        self._poison_spawn_chance = poison_spawn_chance

    def update(self, world: World) -> None:
        """Maintain regular apple and occasionally spawn poisoned apple.

        Args:
            world: ECS world containing entities and components
        """
        grid_size = world.board.cell_size

        # separate regular and poisoned apples
        regular_apples = []
        poisoned_apples = []

        all_apples = world.registry.query_by_type(EntityType.APPLE)
        for entity_id, apple in all_apples.items():
            if hasattr(apple, "poisoned") and apple.poisoned.deadly:
                poisoned_apples.append((entity_id, apple))
            else:
                regular_apples.append((entity_id, apple))

        # ensure exactly 1 regular apple exists
        if len(regular_apples) == 0:
            position = self._find_valid_position(world)
            if position:
                x, y = position
                create_apple(world, x=x, y=y, grid_size=grid_size, color=None)

        # occasionally spawn poisoned apple
        # only spawn if no poisoned apple exists and random chance succeeds
        if len(poisoned_apples) == 0 and random.random() < self._poison_spawn_chance:
            position = self._find_valid_position(world)
            if position:
                x, y = position
                create_poisoned_apple(world, x=x, y=y, grid_size=grid_size, color=None)

    def _find_valid_position(self, world: World) -> Optional[tuple[int, int]]:
        """Find a valid position to spawn an apple.

        A valid position is one that:
        - Is within board bounds
        - Doesn't overlap with snake head
        - Doesn't overlap with snake body segments
        - Doesn't overlap with obstacles
        - Doesn't overlap with existing apples

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

        # get existing apple positions (both regular and poisoned)
        apples = world.registry.query_by_type(EntityType.APPLE)
        for _, apple in apples.items():
            if hasattr(apple, "position"):
                occupied.add((apple.position.x, apple.position.y))

        return occupied
