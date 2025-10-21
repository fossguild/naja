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


# difficulty percentages for obstacle count
DIFFICULTY_PERCENTAGES = {
    "None": 0.0,
    "Easy": 0.04,
    "Medium": 0.06,
    "Hard": 0.10,
    "Impossible": 0.15,
}


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
        """Check for obstacle generation requests.

        This method is called every tick. It can be triggered by:
        - Initial game setup
        - Settings changes (difficulty)
        - Map regeneration requests

        Args:
            world: ECS world containing entities and components
        """
        # stub implementation - will be connected to event system
        # when event handling is implemented in future issues

    def generate_obstacles(
        self, world: World, count: int, snake_start_pos: tuple[int, int]
    ) -> list[int]:
        """Generate obstacles using constructive algorithm with validation.

        Args:
            world: ECS world to generate obstacles in
            count: Number of obstacles to generate
            snake_start_pos: Snake starting position (x, y) for safe zone

        Returns:
            List of entity IDs of generated obstacles
        """
        if count == 0:
            return []

        board = world.board
        grid_size = board.cell_size

        # try multiple times to generate a valid configuration
        for _ in range(self._max_retries):
            obstacle_ids = []
            obstacle_positions = set()

            # get available positions (excluding safe zone)
            available_positions = self._get_available_positions(
                board, grid_size, snake_start_pos
            )
            random.shuffle(available_positions)

            temp_available = list(available_positions)

            # add obstacles one by one with validation
            while len(obstacle_ids) < count and temp_available:
                candidate_pos = temp_available.pop()

                # check if obstacle would create a trap
                if self._would_create_trap(
                    candidate_pos, obstacle_positions, board, grid_size
                ):
                    continue

                # create obstacle entity
                obstacle_id = self._create_obstacle_entity(
                    world, candidate_pos[0], candidate_pos[1]
                )
                obstacle_ids.append(obstacle_id)
                obstacle_positions.add(candidate_pos)

            # verify grid connectivity
            if len(obstacle_ids) == count and self._is_grid_connected(
                obstacle_positions, snake_start_pos, board, grid_size
            ):
                return obstacle_ids

            # failed attempt, remove created obstacles
            for obstacle_id in obstacle_ids:
                world.registry.remove(obstacle_id)

        # exhausted all attempts, generate with fewer obstacles
        print(
            f"Warning: Could not place all {count} obstacles after {self._max_retries} attempts"
        )

        # try one more time with progressive reduction
        for reduced_count in range(count - 1, 0, -1):
            result = self._try_generate_reduced(
                world, reduced_count, snake_start_pos, board, grid_size
            )
            if result:
                print(f"Successfully placed {reduced_count} obstacles instead")
                return result

        return []

    def generate_obstacles_by_difficulty(
        self,
        world: World,
        difficulty: str,
        snake_start_pos: tuple[int, int],
    ) -> list[int]:
        """Generate obstacles based on difficulty level.

        Args:
            world: ECS world to generate obstacles in
            difficulty: Difficulty level string (None, Easy, Medium, Hard, Impossible)
            snake_start_pos: Snake starting position (x, y)

        Returns:
            List of entity IDs of generated obstacles
        """
        board = world.board
        grid_size = board.cell_size

        # calculate obstacle count from difficulty
        count = self.calculate_obstacle_count(board, grid_size, difficulty)

        return self.generate_obstacles(world, count, snake_start_pos)

    @staticmethod
    def calculate_obstacle_count(board, _grid_size: int, difficulty: str) -> int:
        """Calculate number of obstacles from difficulty level.

        Args:
            board: Game board
            grid_size: Size of each grid cell
            difficulty: Difficulty level string

        Returns:
            Number of obstacles to generate
        """
        total_cells = (board.width // _grid_size) * (board.height // _grid_size)
        percentage = DIFFICULTY_PERCENTAGES.get(difficulty, 0.0)
        return int(total_cells * percentage)

    def _get_available_positions(
        self,
        board,
        grid_size: int,
        snake_start_pos: tuple[int, int],
    ) -> list[tuple[int, int]]:
        """Get all valid positions for obstacle placement.

        Args:
            board: Game board
            grid_size: Size of each grid cell
            snake_start_pos: Snake starting position (x, y)

        Returns:
            List of (x, y) positions excluding safe zone
        """
        available = []
        snake_x, snake_y = snake_start_pos

        for x in range(0, board.width, grid_size):
            for y in range(0, board.height, grid_size):
                # exclude safe zone around snake start
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
        """Check if placing obstacle would create a trap.

        A trap is a free cell with 3 or more blocked sides.

        Args:
            new_pos: Position to test (x, y)
            existing_positions: Set of existing obstacle positions
            board: Game board
            grid_size: Size of each grid cell

        Returns:
            True if would create trap, False otherwise
        """
        new_x, new_y = new_pos

        # check four neighbors of the new obstacle
        for dx, dy in [
            (0, grid_size),
            (0, -grid_size),
            (grid_size, 0),
            (-grid_size, 0),
        ]:
            neighbor_x, neighbor_y = new_x + dx, new_y + dy

            # skip if neighbor is already blocked
            if self._is_blocked(
                neighbor_x,
                neighbor_y,
                (0, 0),  # dummy new position
                existing_positions,
                board,
                grid_size,
            ):
                continue

            # count blocked sides of this free neighbor
            blocked_sides = 0

            sides_to_check = [
                (neighbor_x + grid_size, neighbor_y),  # right
                (neighbor_x - grid_size, neighbor_y),  # left
                (neighbor_x, neighbor_y + grid_size),  # down
                (neighbor_x, neighbor_y - grid_size),  # up
            ]

            for side_x, side_y in sides_to_check:
                if self._is_blocked(
                    side_x,
                    side_y,
                    new_pos,
                    existing_positions,
                    board,
                    grid_size,
                ):
                    blocked_sides += 1

            # trap detected: 3 or more blocked sides
            if blocked_sides >= 3:
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
        """Check if a position is blocked.

        Args:
            x: X coordinate
            y: Y coordinate
            new_pos: Position being tested as new obstacle
            existing_positions: Set of existing obstacle positions
            board: Game board
            grid_size: Size of each grid cell

        Returns:
            True if blocked, False if free
        """
        # out of bounds
        if not (0 <= x < board.width and 0 <= y < board.height):
            return True

        # the new obstacle position
        if (x, y) == new_pos:
            return True

        # existing obstacle
        if (x, y) in existing_positions:
            return True

        return False

    def _is_grid_connected(
        self,
        obstacle_positions: set[tuple[int, int]],
        snake_start_pos: tuple[int, int],
        board,
        grid_size: int,
    ) -> bool:
        """Check if grid remains fully connected using flood fill (BFS).

        Args:
            obstacle_positions: Set of obstacle positions
            snake_start_pos: Snake starting position (x, y)
            board: Game board
            grid_size: Size of each grid cell

        Returns:
            True if all free cells are reachable, False otherwise
        """
        # snake start must not be blocked
        if snake_start_pos in obstacle_positions:
            return False

        # calculate expected free cells
        total_cells = (board.width // grid_size) * (board.height // grid_size)
        total_free_cells = total_cells - len(obstacle_positions)

        # flood fill from snake start position
        queue = [snake_start_pos]
        visited = {snake_start_pos}

        while queue:
            x, y = queue.pop(0)

            # check all four neighbors
            for dx, dy in [
                (0, grid_size),
                (0, -grid_size),
                (grid_size, 0),
                (-grid_size, 0),
            ]:
                neighbor = (x + dx, y + dy)

                # add unvisited free neighbors
                if (
                    0 <= neighbor[0] < board.width
                    and 0 <= neighbor[1] < board.height
                    and neighbor not in obstacle_positions
                    and neighbor not in visited
                ):
                    visited.add(neighbor)
                    queue.append(neighbor)

        # grid is connected if all free cells were reached
        return len(visited) == total_free_cells

    def _try_generate_reduced(
        self,
        world: World,
        count: int,
        snake_start_pos: tuple[int, int],
        board,
        grid_size: int,
    ) -> Optional[list[int]]:
        """Try to generate with reduced obstacle count.

        Args:
            world: ECS world
            count: Reduced obstacle count
            snake_start_pos: Snake starting position
            board: Game board
            grid_size: Size of each grid cell

        Returns:
            List of obstacle IDs if successful, None otherwise
        """
        obstacle_ids = []
        obstacle_positions = set()

        available_positions = self._get_available_positions(
            board, grid_size, snake_start_pos
        )
        random.shuffle(available_positions)
        temp_available = list(available_positions)

        while len(obstacle_ids) < count and temp_available:
            candidate_pos = temp_available.pop()

            if self._would_create_trap(
                candidate_pos, obstacle_positions, board, grid_size
            ):
                continue

            obstacle_id = self._create_obstacle_entity(
                world, candidate_pos[0], candidate_pos[1]
            )
            obstacle_ids.append(obstacle_id)
            obstacle_positions.add(candidate_pos)

        if len(obstacle_ids) == count and self._is_grid_connected(
            obstacle_positions, snake_start_pos, board, grid_size
        ):
            return obstacle_ids

        # cleanup on failure
        for obstacle_id in obstacle_ids:
            world.registry.remove(obstacle_id)

        return None

    def _create_obstacle_entity(
        self, world: World, x: int, y: int
    ) -> int:
        """Create a new obstacle entity at specified position.

        Args:
            world: ECS world to create entity in
            x: X position (grid-aligned)
            y: Y position (grid-aligned)

        Returns:
            Entity ID of created obstacle
        """
        # create obstacle entity with required components
        obstacle = ObstacleEntity(
            position=Position(x=x, y=y),
            tag=ObstacleTag(),
        )

        # register entity with world
        entity_id = world.registry.add(obstacle)

        return entity_id
