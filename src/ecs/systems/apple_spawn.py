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

"""Apple spawn system for maintaining correct number of apples in the game.

This system ensures that the game always has the desired number of apples
as configured in the AppleConfig component.
"""

from __future__ import annotations
import random
from typing import Optional

from src.ecs.systems.base_system import BaseSystem
from src.ecs.world import World
from src.ecs.entities.entity import EntityType
from src.ecs.prefabs.apple import create_apple


class AppleSpawnSystem(BaseSystem):
    """System for maintaining the correct number of apples in the game."""

    def __init__(self, max_spawn_attempts: int = 1000):
        self._max_spawn_attempts = max_spawn_attempts

    def update(self, world: World) -> None:
        """Check apple count and spawn new apples if needed."""
        desired_count = self._get_desired_apple_count(world)
        if desired_count <= 0:
            return

        current_apples = world.registry.query_by_type(EntityType.APPLE)
        apples_to_spawn = desired_count - len(current_apples)
        if apples_to_spawn <= 0:
            return

        grid_width = world.board.width
        grid_height = world.board.height
        total_cells = grid_width * grid_height

        occupied = self._get_occupied_positions(world)

        # --- Direct full-board check ---
        free_cells = total_cells - len(occupied)
        if free_cells <= 0:
            # Board is full, nothing to spawn
            return

        # Limit apples_to_spawn to the number of free cells
        apples_to_spawn = min(apples_to_spawn, free_cells)

        for _ in range(apples_to_spawn):
            position = self._find_valid_position(world, grid_width, grid_height, occupied)
            if position:
                x, y = position
                create_apple(world, x=x, y=y, grid_size=world.board.cell_size, color=None)
                occupied.add(position)  # Update occupied positions

    def _get_desired_apple_count(self, world: World) -> int:
        """Return the desired number of apples from AppleConfig, defaulting to 1."""
        config_entities = world.registry.query_by_component("apple_config")
        if config_entities:
            config_entity = list(config_entities.values())[0]
            if hasattr(config_entity, "apple_config"):
                return config_entity.apple_config.desired_count
        return 1

    def _find_valid_position(
        self, world: World, width: int, height: int, occupied: set[tuple[int, int]]
    ) -> Optional[tuple[int, int]]:
        """Try to find a valid position to spawn an apple."""
        for _ in range(self._max_spawn_attempts):
            x = random.randint(0, width - 1)
            y = random.randint(0, height - 1)
            if (x, y) not in occupied:
                return (x, y)
        return None

    def _get_occupied_positions(self, world: World) -> set[tuple[int, int]]:
        """Return all positions currently occupied by game entities."""
        occupied = set()

        # Snakes
        snakes = world.registry.query_by_type(EntityType.SNAKE)
        for _, snake in snakes.items():
            if hasattr(snake, "position"):
                occupied.add((snake.position.x, snake.position.y))
            if hasattr(snake, "body"):
                for segment in snake.body.segments:
                    occupied.add((segment.x, segment.y))

        # Obstacles
        obstacles = world.registry.query_by_type(EntityType.OBSTACLE)
        for _, obs in obstacles.items():
            if hasattr(obs, "position"):
                occupied.add((obs.position.x, obs.position.y))

        # Existing apples
        apples = world.registry.query_by_type(EntityType.APPLE)
        for _, apple in apples.items():
            if hasattr(apple, "position"):
                occupied.add((apple.position.x, apple.position.y))

        return occupied

    def set_max_spawn_attempts(self, max_attempts: int) -> None:
        """Set the maximum number of spawn attempts."""
        self._max_spawn_attempts = max(1, max_attempts)

    def get_max_spawn_attempts(self) -> int:
        """Get the current maximum number of spawn attempts."""
        return self._max_spawn_attempts
