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

"""Trail generation system for Trail Mode.

This system creates permanent obstacles at positions where the snake's head
has been, progressively filling the board as the game continues.
"""

from __future__ import annotations

from ecs.systems.base_system import BaseSystem
from ecs.world import World
from ecs.entities.entity import EntityType
from ecs.entities.trail_obstacle import TrailObstacle
from ecs.components.position import Position
from ecs.components.trail_obstacle import TrailObstacleTag
from ecs.components.renderable import Renderable
from core.types.color import Color


# Trail obstacle color - darker than regular obstacles for distinction
TRAIL_OBSTACLE_COLOR = "#4a4a4a"


class TrailGenerationSystem(BaseSystem):
    """System for generating trail obstacles in Trail Mode.

    Reads: Position (snake head), GameState (trail_mode_enabled)
    Writes: New TrailObstacle entities, GameState.trail_obstacles

    Responsibilities:
    - Track snake head's previous positions
    - Create trail obstacle entities when snake moves
    - Update game state's trail obstacles list
    - Only activate when trail_mode_enabled is True

    The system creates a permanent obstacle at each position the snake's
    head moves from, making the game progressively more difficult.
    """

    def __init__(self):
        """Initialize the trail generation system.
        
        Tracks the snake's previous head position to determine where
        to place trail obstacles.
        """
        self._previous_head_positions = {}  # {entity_id: (x, y)}

    def update(self, world: World) -> None:
        """Update trail obstacles based on snake movement.

        Args:
            world: ECS world instance
        """
        # Check if Trail Mode is enabled
        game_state_entities = world.registry.query_by_component("game_state")
        if not game_state_entities:
            return

        game_state_entity = next(iter(game_state_entities.values()))
        if not hasattr(game_state_entity, "game_state"):
            return

        game_state = game_state_entity.game_state

        # Only process if trail mode is enabled and game has started
        if not game_state.trail_mode_enabled or not game_state.game_started:
            return

        # Get all snakes
        snakes = world.registry.query_by_type_and_components(
            EntityType.SNAKE, "position", "body"
        )

        for entity_id, snake in snakes.items():
            # Skip dead snakes
            if not snake.body.alive:
                continue

            current_pos = (snake.position.x, snake.position.y)

            # Check if we have a previous position for this snake
            if entity_id in self._previous_head_positions:
                prev_pos = self._previous_head_positions[entity_id]

                # If the snake has moved, create a trail obstacle at the previous position
                if prev_pos != current_pos:
                    # Don't create trail obstacle if one already exists at this position
                    if prev_pos not in game_state.trail_obstacles:
                        self._create_trail_obstacle(world, prev_pos[0], prev_pos[1])
                        game_state.trail_obstacles.append(prev_pos)

            # Update the previous position for next frame
            self._previous_head_positions[entity_id] = current_pos

    def _create_trail_obstacle(self, world: World, x: int, y: int) -> int:
        """Create a trail obstacle entity at the specified position.

        Args:
            world: ECS world instance
            x: X coordinate for the obstacle
            y: Y coordinate for the obstacle

        Returns:
            Entity ID of the created trail obstacle
        """
        grid_size = world.board.cell_size
        color = Color.from_hex(TRAIL_OBSTACLE_COLOR)

        trail_obstacle = TrailObstacle(
            position=Position(x=x, y=y),
            tag=TrailObstacleTag(),
            renderable=Renderable(
                shape="square",
                color=color,
                size=grid_size,
            ),
        )

        return world.registry.add(trail_obstacle)
