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

"""Obstacle generation system with connectivity and trap guarantees.

This system generates obstacles using a constructive algorithm that ensures:
- The grid remains fully connected (flood fill check)
- No inescapable traps are created
- Safe distance from snake starting position
- Deterministic generation with seed support
"""

from __future__ import annotations

import random
from typing import Optional

from src.ecs.systems.base_system import BaseSystem
from src.ecs.world import World
from src.ecs.entities.obstacle_field import Obstacle as ObstacleEntity
from src.ecs.components.position import Position
from src.ecs.components.obstacle import ObstacleTag
from src.game import constants


# grid directions (up, down, left, right)
GRID_DIRECTIONS = [(0, 1), (0, -1), (1, 0), (-1, 0)]


class ObstacleGenerationSystem(BaseSystem):
    """System for generating obstacles with connectivity and trap guarantees.

    Reads: Position (snake), Board (dimensions)
    Writes: New entities (Obstacle)
    Queries: entities with Position (to determine safe zone)

    Responsibilities:
    - Generate obstacles based on difficulty level
    - Ensure grid connectivity (flood fill algorithm)
    - Prevent inescapable traps (3+ blocked sides)
    - Maintain safe distance from snake start
    - Support deterministic generation with seed

    Note: This system uses constructive generation - obstacles are added
    one at a time with validation after each placement.
    """

    def __init__(
        self,
        max_retries: int = 100,
        safe_zone_width: int = 8,
        safe_zone_height: int = 2,
        random_seed: Optional[int] = None,
    ):
        """Initialize the ObstacleGenerationSystem.

        Args:
            max_retries: Maximum attempts to generate valid map
            safe_zone_width: Grid cells width for snake safe zone
            safe_zone_height: Grid cells height for snake safe zone
            random_seed: Optional seed for deterministic generation (testing)
        """
        self._max_retries = max_retries
        self._safe_zone_width = safe_zone_width
        self._safe_zone_height = safe_zone_height
        if random_seed is not None:
            random.seed(random_seed)

    def update(self, world: World) -> None:
        """Check for obstacle generation requests (stub for event system)."""
        # will be connected to event system in future

    def generate_obstacles(
        self, world: World, count: int, snake_start_pos: tuple[int, int]
    ) -> list[int]:
        """Generate obstacles using constructive algorithm with validation."""
        if count == 0:
            return []

        board, grid_size = world.board, world.board.cell_size

        # try multiple times with original count
        for _ in range(self._max_retries):
            result = self._attempt_generation(
                world, count, snake_start_pos, board, grid_size
            )
            if result:
                return result

        # try with progressively fewer obstacles
        print(
            f"Warning: Could not place {count} obstacles after {self._max_retries} attempts"
        )
        for reduced_count in range(count - 1, 0, -1):
            result = self._attempt_generation(
                world, reduced_count, snake_start_pos, board, grid_size
            )
            if result:
                print(f"Successfully placed {reduced_count} obstacles instead")
                return result

        return []

    def _attempt_generation(
        self,
        world: World,
        count: int,
        snake_start_pos: tuple[int, int],
        board,
        grid_size: int,
    ) -> Optional[list[int]]:
        """Attempt to generate obstacles with validation."""
        obstacle_ids, obstacle_positions = [], set()
        available = self._get_available_positions(board, grid_size, snake_start_pos)
        random.shuffle(available)

        # place obstacles one by one with validation
        while len(obstacle_ids) < count and available:
            candidate = available.pop()
            if self._would_create_trap(candidate, obstacle_positions, board, grid_size):
                continue
            obstacle_id = self._create_obstacle_entity(
                world, candidate[0], candidate[1]
            )
            obstacle_ids.append(obstacle_id)
            obstacle_positions.add(candidate)

        # verify success
        if len(obstacle_ids) == count and self._is_grid_connected(
            obstacle_positions, snake_start_pos, board, grid_size
        ):
            return obstacle_ids

        # cleanup failed attempt
        for obstacle_id in obstacle_ids:
            world.registry.remove(obstacle_id)
        return None

    def generate_obstacles_by_difficulty(
        self, world: World, difficulty: str, snake_start_pos: tuple[int, int]
    ) -> list[int]:
        """Generate obstacles based on difficulty level."""
        board, grid_size = world.board, world.board.cell_size
        count = self.calculate_obstacle_count(board, grid_size, difficulty)
        return self.generate_obstacles(world, count, snake_start_pos)

    @staticmethod
    def calculate_obstacle_count(board, _grid_size: int, difficulty: str) -> int:
        """Calculate number of obstacles from difficulty level."""
        total_cells = (board.width // _grid_size) * (board.height // _grid_size)
        return int(total_cells * constants.DIFFICULTY_PERCENTAGES.get(difficulty, 0.0))

    def _get_available_positions(
        self, board, grid_size: int, snake_start_pos: tuple[int, int]
    ) -> list[tuple[int, int]]:
        """Get all valid positions excluding safe zone around snake start."""
        snake_x, snake_y = snake_start_pos
        available = []
        for x in range(0, board.width, grid_size):
            for y in range(0, board.height, grid_size):
                if not (
                    abs(x - snake_x) < grid_size * self._safe_zone_width
                    and abs(y - snake_y) < grid_size * self._safe_zone_height
                ):
                    available.append((x, y))
        return available

    def _would_create_trap(
        self,
        new_pos: tuple[int, int],
        existing_positions: set[tuple[int, int]],
        board,
        grid_size: int,
    ) -> bool:
        """Check if placing obstacle would create a trap (3+ blocked sides)."""
        new_x, new_y = new_pos

        # check each neighbor of the new obstacle
        for dx, dy in GRID_DIRECTIONS:
            neighbor = (new_x + dx * grid_size, new_y + dy * grid_size)

            # skip if neighbor already blocked
            if self._is_blocked(
                neighbor[0], neighbor[1], (0, 0), existing_positions, board, grid_size
            ):
                continue

            # count how many sides of this free neighbor would be blocked
            blocked_sides = sum(
                1
                for ndx, ndy in GRID_DIRECTIONS
                if self._is_blocked(
                    neighbor[0] + ndx * grid_size,
                    neighbor[1] + ndy * grid_size,
                    new_pos,
                    existing_positions,
                    board,
                    grid_size,
                )
            )

            if blocked_sides >= 3:  # trap detected
                return True

        return False

    def _is_blocked(
        self,
        x: int,
        y: int,
        new_pos: tuple[int, int],
        existing_positions: set[tuple[int, int]],
        board,
        grid_size: int,
    ) -> bool:
        """Check if position is blocked (out of bounds, new obstacle, or existing obstacle)."""
        return (
            not (0 <= x < board.width and 0 <= y < board.height)
            or (x, y) == new_pos
            or (x, y) in existing_positions
        )

    def _is_grid_connected(
        self,
        obstacle_positions: set[tuple[int, int]],
        snake_start_pos: tuple[int, int],
        board,
        grid_size: int,
    ) -> bool:
        """Check if grid remains fully connected using flood fill (BFS)."""
        if snake_start_pos in obstacle_positions:
            return False

        # calculate expected free cells
        total_cells = (board.width // grid_size) * (board.height // grid_size)
        expected_free = total_cells - len(obstacle_positions)

        # flood fill from snake start
        queue, visited = [snake_start_pos], {snake_start_pos}
        while queue:
            x, y = queue.pop(0)
            for dx, dy in GRID_DIRECTIONS:
                neighbor = (x + dx * grid_size, y + dy * grid_size)
                if (
                    0 <= neighbor[0] < board.width
                    and 0 <= neighbor[1] < board.height
                    and neighbor not in obstacle_positions
                    and neighbor not in visited
                ):
                    visited.add(neighbor)
                    queue.append(neighbor)

        return len(visited) == expected_free

    def _create_obstacle_entity(self, world: World, x: int, y: int) -> int:
        """Create obstacle entity at specified position."""
        obstacle = ObstacleEntity(position=Position(x=x, y=y), tag=ObstacleTag())
        return world.registry.add(obstacle)
