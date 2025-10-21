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

"""Movement system."""

from __future__ import annotations

from dataclasses import replace

from src.ecs.systems.base_system import BaseSystem
from src.ecs.world import World
from src.ecs.entities.entity import EntityType
from src.ecs.components.position import Position
from src.ecs.components.velocity import Velocity
from src.ecs.components.snake_body import SnakeBody


class MovementSystem(BaseSystem):
    """Update entity positions based on velocity and grid rules.

    Reads: Position, Velocity, SnakeBody, Board (size)
    Writes: Position, SnakeBody.segments

    """

    def __init__(self):
        """Initialize movement system with timing control."""
        self._frame_counter = 0
        self._frames_per_move = 12  # move every 12 frames (at 60fps = 5 moves/second)

    def update(self, world: World) -> None:
        # simple frame-based movement (more reliable than time-based for now)
        self._frame_counter += 1

        # only move every N frames
        if self._frame_counter < self._frames_per_move:
            return

        self._frame_counter = 0

        registry = world.registry
        board = world.board

        # Getting all snake entities in a dictionary
        snakes = registry.query_by_type_and_components(
            EntityType.SNAKE, "position", "velocity", "body"
        )

        # Updating each entity
        for _entity_id, snake in snakes.items():
            position: Position = snake.position
            velocity: Velocity = snake.velocity
            body: SnakeBody = snake.body

            # Verifying if a given snake is alive
            if not body.alive:
                continue

            # only move if velocity is non-zero
            if velocity.dx == 0 and velocity.dy == 0:
                continue

            # Store previous position for smooth interpolation
            position.prev_x = position.x
            position.prev_y = position.y

            # Insert a new segment to the head's current position
            body.segments.insert(0, replace(position))

            # Keep exactly the right number of segments (consistent size)
            # This prevents the tail from growing/shrinking during movement
            desired_tail_len = max(0, body.size - 1)
            if len(body.segments) > desired_tail_len:
                # Remove excess segments from the end
                body.segments = body.segments[:desired_tail_len]
            elif len(body.segments) < desired_tail_len:
                # Add missing segments at the end (duplicate last position)
                if body.segments:
                    last_segment = body.segments[-1]
                    for _ in range(desired_tail_len - len(body.segments)):
                        body.segments.append(replace(last_segment))

            # Move head by exactly one grid cell in velocity direction
            new_x = (position.x + velocity.dx) % board.width
            new_y = (position.y + velocity.dy) % board.height

            position.x = new_x
            position.y = new_y

            # Reset interpolation alpha to 0.0 for smooth animation from old to new position
            if hasattr(snake, "interpolation"):
                snake.interpolation.alpha = 0.0
