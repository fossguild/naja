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
    """System for maintaining the correct number of apples in the game.
    
    Reads: AppleConfig (desired count), Apple entities (current count)
    Writes: Creates new apple entities as needed
    
    Responsibilities:
    - Count current number of apples in the world
    - Compare with desired count from AppleConfig
    - Spawn new apples if count is below desired
    - Find valid spawn positions (avoiding snake, obstacles, other apples)
    
    This system runs after collision detection to respawn apples that were eaten.
    """

    def __init__(self, max_spawn_attempts: int = 1000):
        """Initialize the AppleSpawnSystem.
        
        Args:
            max_spawn_attempts: Maximum attempts to find a valid spawn position
        """
        self._max_spawn_attempts = max_spawn_attempts

    def update(self, world: World) -> None:
        """Check apple count and spawn new apples if needed.
        
        Args:
            world: ECS world containing entities and components
        """
        # Get desired apple count from config
        desired_count = self._get_desired_apple_count(world)
        
        if desired_count <= 0:
            return
        
        # Count current apples
        current_apples = world.registry.query_by_type(EntityType.APPLE)
        current_count = len(current_apples)
        
        # Spawn new apples if we're below desired count
        apples_to_spawn = desired_count - current_count
        
        if apples_to_spawn > 0:
            grid_size = world.board.cell_size
            
            for _ in range(apples_to_spawn):
                position = self._find_valid_position(world)
                if position:
                    x, y = position
                    create_apple(world, x=x, y=y, grid_size=grid_size, color=None)

    def _get_desired_apple_count(self, world: World) -> int:
        """Get the desired number of apples from AppleConfig component.
        
        Args:
            world: ECS world
            
        Returns:
            Desired apple count, or 1 if no config found
        """
        # Query for entities with AppleConfig component
        config_entities = world.registry.query_by_component("apple_config")
        
        if config_entities:
            config_entity = list(config_entities.values())[0]
            if hasattr(config_entity, "apple_config"):
                return config_entity.apple_config.desired_count
        
        return 1  # Default to 1 apple

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
        
        # Get occupied positions
        occupied = self._get_occupied_positions(world)
        
        # Try to find a valid position
        for _ in range(self._max_spawn_attempts):
            x = random.randint(0, board.width - 1)
            y = random.randint(0, board.height - 1)
            
            if (x, y) not in occupied:
                return (x, y)
        
        # If we couldn't find a position after max attempts, return None
        # This can happen in very cramped situations
        return None

    def _get_occupied_positions(self, world: World) -> set[tuple[int, int]]:
        """Get all positions currently occupied by game entities.
        
        Args:
            world: ECS world
            
        Returns:
            Set of (x, y) tuples representing occupied positions
        """
        occupied = set()
        
        # Get snake positions
        snakes = world.registry.query_by_type(EntityType.SNAKE)
        for _, snake in snakes.items():
            if hasattr(snake, "position"):
                # Add head position
                occupied.add((snake.position.x, snake.position.y))
                
                # Add body segments
                if hasattr(snake, "body"):
                    for segment in snake.body.segments:
                        occupied.add((segment.x, segment.y))
        
        # Get obstacle positions
        obstacles = world.registry.query_by_type(EntityType.OBSTACLE)
        for _, obstacle in obstacles.items():
            if hasattr(obstacle, "position"):
                occupied.add((obstacle.position.x, obstacle.position.y))
        
        # Get existing apple positions
        apples = world.registry.query_by_type(EntityType.APPLE)
        for _, apple in apples.items():
            if hasattr(apple, "position"):
                occupied.add((apple.position.x, apple.position.y))
        
        return occupied

    def set_max_spawn_attempts(self, max_attempts: int) -> None:
        """Set the maximum number of spawn attempts.
        
        Args:
            max_attempts: New maximum attempts value
        """
        self._max_spawn_attempts = max(1, max_attempts)

    def get_max_spawn_attempts(self) -> int:
        """Get the current maximum spawn attempts.
        
        Returns:
            Current maximum spawn attempts
        """
        return self._max_spawn_attempts
