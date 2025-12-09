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

"""Portal Barrier Spawn System - spawns portal barriers after eating apples."""

import random
from ecs.systems.base_system import BaseSystem
from ecs.world import World
from ecs.entities.entity import EntityType


class PortalBarrierSpawnSystem(BaseSystem):
    """System responsible for spawning portal barriers in Portal Barrier Mode.

    Spawns a new portal barrier after every 2 apples are eaten.

    Responsibilities:
    - Track apple consumption
    - Spawn portal barriers at regular intervals (every 2 apples)
    - Ensure barriers don't overlap with existing obstacles or barriers
    """

    def __init__(self):
        """Initialize the PortalBarrierSpawnSystem."""
        self._apples_eaten_count = 0
        self._last_apple_count = 0

    def update(self, world: World) -> None:
        """Update method to spawn portal barriers when needed.

        Args:
            world: Game world
        """
        # Get the score entity to track apples eaten
        score_entity = self._get_score_entity(world)
        if not score_entity or not hasattr(score_entity, "score"):
            return

        current_score = score_entity.score.current

        # Calculate how many apples have been eaten
        # Assuming each apple is worth some base points
        # We need to count total apples eaten (every 2 apples spawn a barrier)
        apples_eaten = self._count_apples_eaten(world, current_score)

        # Check if we should spawn a new barrier (every 2 apples)
        if apples_eaten >= self._last_apple_count + 2:
            self._spawn_portal_barrier(world)
            self._last_apple_count = apples_eaten

    def _get_score_entity(self, world: World):
        """Get the score entity from the world.

        Args:
            world: ECS world

        Returns:
            Score entity or None if not found
        """
        # Query for entity with score component
        score_entities = world.registry.query_by_component("score")
        if score_entities:
            return next(iter(score_entities.values()))
        return None

    def _count_apples_eaten(self, world: World, current_score: int) -> int:
        """Count how many apples have been eaten based on score.

        Args:
            world: ECS world
            current_score: Current game score

        Returns:
            Number of apples eaten (each apple gives 10 points)
        """
        # Standard apple value is 10 points
        return current_score // 10

    def _spawn_portal_barrier(self, world: World) -> None:
        """Spawn a single portal barrier at a random valid position.

        Args:
            world: ECS world
        """
        from ecs.prefabs.portal_barrier import create_portal_barrier

        grid_size = world.board.cell_size

        # Get occupied positions
        occupied_positions = set()

        # Snake positions
        snakes = world.registry.query_by_type(EntityType.SNAKE)
        for _, snake in snakes.items():
            if hasattr(snake, "position"):
                occupied_positions.add((snake.position.x, snake.position.y))
                if hasattr(snake, "body"):
                    for segment in snake.body.segments:
                        occupied_positions.add((segment.x, segment.y))

        # Apple positions
        apples = world.registry.query_by_type(EntityType.APPLE)
        for _, apple in apples.items():
            if hasattr(apple, "position"):
                occupied_positions.add((apple.position.x, apple.position.y))

        # Obstacle positions
        obstacles = world.registry.query_by_type(EntityType.OBSTACLE)
        for _, obstacle in obstacles.items():
            if hasattr(obstacle, "position"):
                occupied_positions.add((obstacle.position.x, obstacle.position.y))

        # Existing portal barrier positions
        portal_barriers = world.registry.query_by_type(EntityType.PORTAL_BARRIER)
        for _, barrier in portal_barriers.items():
            if hasattr(barrier, "portal_barrier"):
                occupied_positions.add(
                    (barrier.portal_barrier.block1_x, barrier.portal_barrier.block1_y)
                )
                occupied_positions.add(
                    (barrier.portal_barrier.block2_x, barrier.portal_barrier.block2_y)
                )

        # Try to spawn a barrier
        attempts = 0
        max_attempts = 100

        while attempts < max_attempts:
            # Pick random position for first block
            block1_x = random.randint(1, world.board.width - 2)
            block1_y = random.randint(1, world.board.height - 2)

            # Pick random direction for second block (horizontal or vertical)
            is_horizontal = random.choice([True, False])

            if is_horizontal:
                # Second block is to the right or left of first
                block2_x = block1_x + random.choice([1, -1])
                block2_y = block1_y
            else:
                # Second block is above or below first
                block2_x = block1_x
                block2_y = block1_y + random.choice([1, -1])

            # Check if second block is within bounds
            if (
                block2_x < 0
                or block2_x >= world.board.width
                or block2_y < 0
                or block2_y >= world.board.height
            ):
                attempts += 1
                continue

            # Check if positions are not occupied
            if (block1_x, block1_y) in occupied_positions or (
                block2_x,
                block2_y,
            ) in occupied_positions:
                attempts += 1
                continue

            # Create the portal barrier
            create_portal_barrier(
                world,
                block1_x=block1_x,
                block1_y=block1_y,
                block2_x=block2_x,
                block2_y=block2_y,
                grid_size=grid_size,
                color=(0, 255, 255),  # cyan
            )

            print(
                f"Portal barrier spawned at ({block1_x}, {block1_y}) <-> ({block2_x}, {block2_y})"
            )
            return

        # Could not find a valid position after max attempts
        print("Failed to spawn portal barrier - no valid position found")
