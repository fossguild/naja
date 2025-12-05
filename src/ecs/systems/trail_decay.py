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

"""Trail decay system for Trail Mode.

This system handles the gradual decay of trail obstacles, making them
disappear after a certain number of snake moves. This adds strategic
depth to the game as players can wait for trails to decay to free paths.
"""

from __future__ import annotations

from ecs.systems.base_system import BaseSystem
from ecs.world import World
from ecs.entities.entity import EntityType
from core.types.color import Color


# Base color for trail obstacles (used for fade calculations)
TRAIL_OBSTACLE_BASE_COLOR = "#4a4a4a"


class TrailDecaySystem(BaseSystem):
    """System for decaying and removing trail obstacles over time.

    Reads: TrailObstacleTag (ttl), GameState (trail_mode_enabled), Position
    Writes: TrailObstacleTag (ttl), Renderable (color fade), removes entities

    Responsibilities:
    - Track snake movement to trigger decay
    - Decrement TTL on all trail obstacles when snake moves
    - Update obstacle colors based on remaining TTL (fade effect)
    - Remove trail obstacles when TTL reaches zero
    - Update game state's trail_obstacles list

    The system creates a gradual decay effect, making obstacles fade
    and eventually disappear, adding strategic depth to the game.
    """

    def __init__(self):
        """Initialize the trail decay system.

        Tracks the snake's previous head position to determine when
        to decrement TTL (only when snake actually moves).
        """
        self._previous_head_positions = {}  # {entity_id: (x, y)}

    def update(self, world: World) -> None:
        """Update trail obstacle decay based on snake movement.

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

        # Check if snake has moved
        snake_moved = self._check_snake_moved(world)

        if snake_moved:
            self._decay_obstacles(world, game_state)

    def _check_snake_moved(self, world: World) -> bool:
        """Check if the snake has moved since last update.

        Args:
            world: ECS world instance

        Returns:
            True if the snake moved, False otherwise
        """
        snakes = world.registry.query_by_type_and_components(
            EntityType.SNAKE, "position", "body"
        )

        for entity_id, snake in snakes.items():
            # Skip dead snakes
            if not snake.body.alive:
                continue

            current_pos = (snake.position.x, snake.position.y)

            if entity_id in self._previous_head_positions:
                prev_pos = self._previous_head_positions[entity_id]
                if prev_pos != current_pos:
                    self._previous_head_positions[entity_id] = current_pos
                    return True
            else:
                self._previous_head_positions[entity_id] = current_pos

        return False

    def _decay_obstacles(self, world: World, game_state) -> None:
        """Decrement TTL on all trail obstacles and remove expired ones.

        Args:
            world: ECS world instance
            game_state: GameState component
        """
        # Query all trail obstacles
        obstacles = world.registry.query_by_component("tag")
        entities_to_remove = []
        positions_to_remove = []

        for entity_id, entity in obstacles.items():
            # Check if this is a trail obstacle (has TrailObstacleTag)
            if not hasattr(entity, "tag"):
                continue

            tag = entity.tag
            if not hasattr(tag, "ttl"):
                continue  # Not a trail obstacle

            # Decrement TTL
            tag.ttl -= 1

            if tag.ttl <= 0:
                # Mark for removal
                entities_to_remove.append(entity_id)
                if hasattr(entity, "position"):
                    positions_to_remove.append(
                        (entity.position.x, entity.position.y)
                    )
            else:
                # Update visual fade effect
                self._update_obstacle_fade(entity, tag)

        # Remove expired obstacles
        for entity_id in entities_to_remove:
            world.registry.remove(entity_id)

        # Update game state's trail_obstacles list
        for pos in positions_to_remove:
            if pos in game_state.trail_obstacles:
                game_state.trail_obstacles.remove(pos)

    def _update_obstacle_fade(self, entity, tag) -> None:
        """Update the obstacle's color based on remaining TTL.

        Creates a fade effect as the obstacle ages.

        Args:
            entity: The trail obstacle entity
            tag: The TrailObstacleTag component
        """
        if not hasattr(entity, "renderable") or entity.renderable is None:
            return

        # Calculate fade factor (1.0 = full opacity, 0.0 = invisible)
        fade_factor = tag.ttl / tag.max_ttl

        # Base color components (from #4a4a4a)
        base_r, base_g, base_b = 74, 74, 74

        # Fade towards a lighter color (fading out)
        # We interpolate towards the background-ish color
        target_r, target_g, target_b = 30, 30, 30

        new_r = int(target_r + (base_r - target_r) * fade_factor)
        new_g = int(target_g + (base_g - target_g) * fade_factor)
        new_b = int(target_b + (base_b - target_b) * fade_factor)

        entity.renderable.color = Color(new_r, new_g, new_b)
