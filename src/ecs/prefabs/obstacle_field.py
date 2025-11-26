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

"""Obstacle entity prefab factory."""

import random
from typing import Optional, Literal

from ecs.world import World
from ecs.entities.obstacle_field import Obstacle
from ecs.components.position import Position
from ecs.components.obstacle import ObstacleTag
from ecs.components.renderable import Renderable
from core.types.color import Color
from game import constants


DifficultyLevel = Literal[
    "None",
    "Easy",
    "Medium",
    "Hard",
    "Impossible",
]


def create_obstacles(
    world: World,
    difficulty: DifficultyLevel,
    dynamic_spawn: bool,
    grid_size: int,
    random_seed: Optional[int] = None,
) -> list[int]:
    """Create obstacle entities based on difficulty level.

    Creates obstacles that fill a percentage of the board based on difficulty.
    Difficulties obstacles percentages are defined as DIFFICULTY_PERCENTAGES in
    constants.py.

    Args:
        world: ECS world to create entities in
        difficulty: Difficulty level determining number of obstacles
        dynamic_spawn: Whether to use dynamic spawn mode for obstacles
        grid_size: Size of each grid cell in pixels
        random_seed: Optional seed for deterministic obstacle placement (testing)

    Returns:
        list[int]: List of entity IDs for created obstacles

    Example:
        >>> obstacle_ids = create_obstacles(world, "Medium", False, grid_size=20)
        >>> len(obstacle_ids)  # 6% of total cells
        30
    """
    if random_seed is not None:
        random.seed(random_seed)

    # get board dimensions
    board = world.board

    # board.width and board.height are in TILES, not pixels
    grid_width_tiles = board.width
    grid_height_tiles = board.height

    # calculate total cells (board dimensions are in tiles)
    total_cells = grid_width_tiles * grid_height_tiles

    # calculate number of obstacles based on difficulty
    num_obstacles = _calculate_obstacles_from_difficulty(
        difficulty, dynamic_spawn, total_cells
    )

    if num_obstacles == 0:
        return []

    # get all occupied cells (snake, apples, etc)
    occupied_cells = _get_occupied_cells(world)

    # Add safe zone cells to occupied cells to prevent spawning there
    occupied_cells.update(_get_safe_zone_cells(world))

    # get all available cells for obstacle placement
    available_cells = []
    for tile_x in range(grid_width_tiles):
        for tile_y in range(grid_height_tiles):
            # Use grid coordinates (tiles), not pixel coordinates
            if (tile_x, tile_y) not in occupied_cells:
                available_cells.append((tile_x, tile_y))

    # limit obstacles to available cells
    num_obstacles = min(num_obstacles, len(available_cells))

    # randomly select cells for obstacles
    obstacle_positions = random.sample(available_cells, num_obstacles)

    # create obstacle entities
    obstacle_ids = []
    for i, (x, y) in enumerate(obstacle_positions):
        # Create obstacle with grid coordinates (tiles), not pixels
        obstacle = Obstacle(
            position=Position(x=x, y=y, prev_x=x, prev_y=y),
            tag=ObstacleTag(),
            renderable=Renderable(
                shape="square",
                color=Color.from_hex("#666666"),  # Gray color for obstacles
                size=grid_size,
                layer=0,
            ),
        )
        entity_id = world.registry.add(obstacle)
        obstacle_ids.append(entity_id)

    return obstacle_ids


def _calculate_obstacles_from_difficulty(
    difficulty: DifficultyLevel,
    dynamic_spawn: bool,
    total_cells: int,
) -> int:
    """Calculate number of obstacles based on difficulty and total cells.

    Args:
        difficulty: Difficulty level
        dynamic_spawn: Whether dynamic spawn mode is enabled
        total_cells: Total number of cells in the grid

    Returns:
        int: Number of obstacles to create
    """
    percentage = constants.DIFFICULTY_PERCENTAGES.get(difficulty, 0.0)

    if dynamic_spawn:
        # In dynamic spawn mode, use initial coefficient to reduce the number of obstacles
        percentage *= constants.DYNAMIC_SPAWN_OBSTACLES_INITIAL_COEFFICIENT

    return int(total_cells * percentage)


def _get_occupied_cells(world: World) -> set[tuple[int, int]]:
    """Get set of all occupied cell positions.

    Args:
        world: ECS world to query

    Returns:
        set[tuple[int, int]]: Set of (x, y) tuples representing occupied cells
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
    from ecs.entities.entity import EntityType

    snakes = registry.query_by_type(EntityType.SNAKE)
    for _snake_id, snake in snakes.items():
        if hasattr(snake, "body") and hasattr(snake.body, "segments"):
            for segment in snake.body.segments:
                occupied.add((segment.x, segment.y))

    return occupied


def _get_safe_zone_cells(world: World) -> set[tuple[int, int]]:
    """Get set of safe zone cells where obstacles should not spawn.

    Includes 3 cells in front of the snake's movement direction.

    Args:
        world: ECS world to query

    Returns:
        set[tuple[int, int]]: Set of (x, y) tuples representing safe cells
    """
    safe_cells = set()
    registry = world.registry
    from ecs.entities.entity import EntityType

    snakes = registry.query_by_type(EntityType.SNAKE)
    for _, snake in snakes.items():
        if hasattr(snake, "position") and hasattr(snake, "velocity"):
            head_x, head_y = snake.position.x, snake.position.y
            dx, dy = snake.velocity.dx, snake.velocity.dy

            # Block 3 cells in front of the snake
            # If velocity is 0 (unlikely for snake), we don't block anything extra
            if dx != 0 or dy != 0:
                board = world.board
                for i in range(1, 4):
                    safe_x = head_x + dx * i
                    safe_y = head_y + dy * i
                    # Only add cells within grid boundaries
                    if 0 <= safe_x < board.width and 0 <= safe_y < board.height:
                        safe_cells.add((safe_x, safe_y))

    return safe_cells
