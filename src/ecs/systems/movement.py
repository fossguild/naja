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
from typing import Optional, Callable

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

    def __init__(self, get_electric_walls: Optional[Callable[[], bool]] = None):
        """Initialize movement system with timing control.

        Args:
            get_electric_walls: Optional callback to check if electric walls are enabled.
                               If None, wrapping is always applied (default behavior).
        """
        self._frame_counter = 0
        self._frames_per_move = 12  # move every 12 frames (at 60fps = 5 moves/second)
        self._get_electric_walls = get_electric_walls

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

            # Update all segment positions to follow the one ahead
            # Work backwards to avoid overwriting positions we still need
            # This creates the "caterpillar" following effect

            # Save the old positions before shifting
            if body.segments:
                # Shift all segments backward (each takes the position ahead)
                for i in range(len(body.segments) - 1, 0, -1):
                    # Save where this segment currently is (for prev)
                    old_x = body.segments[i].x
                    old_y = body.segments[i].y

                    # Move this segment to where the segment ahead is
                    body.segments[i].x = body.segments[i - 1].x
                    body.segments[i].y = body.segments[i - 1].y

                    # Set prev to where it was before moving
                    body.segments[i].prev_x = old_x
                    body.segments[i].prev_y = old_y

                # First segment follows the head
                old_x = body.segments[0].x
                old_y = body.segments[0].y
                body.segments[0].x = position.x  # Head's OLD position
                body.segments[0].y = position.y
                body.segments[0].prev_x = old_x
                body.segments[0].prev_y = old_y

            # Maintain correct number of segments based on body size
            desired_tail_len = max(0, body.size - 1)

            # Add or remove segments as needed
            if len(body.segments) > desired_tail_len:
                # Snake shrunk - remove excess segments from the end
                body.segments = body.segments[:desired_tail_len]
            elif len(body.segments) < desired_tail_len:
                # Snake grew - add new segments at the end
                if body.segments:
                    # Add segments at the last segment's position
                    last_segment = body.segments[-1]
                    for _ in range(desired_tail_len - len(body.segments)):
                        new_seg = Position(
                            x=last_segment.x,
                            y=last_segment.y,
                            prev_x=last_segment.x,
                            prev_y=last_segment.y,
                        )
                        body.segments.append(new_seg)
                else:
                    # First segment - create at head's position
                    new_seg = Position(
                        x=position.x,
                        y=position.y,
                        prev_x=position.x,
                        prev_y=position.y,
                    )
                    body.segments.append(new_seg)

            # Move head by exactly one grid cell in velocity direction
            # Only wrap around if electric walls are disabled
            # If electric walls are enabled, collision system will handle out-of-bounds
            electric_walls = (
                self._get_electric_walls() if self._get_electric_walls else False
            )

            if electric_walls:
                # Electric walls mode: don't wrap, let collision system detect wall hit
                new_x = position.x + velocity.dx
                new_y = position.y + velocity.dy
            else:
                # Wrapping mode: wrap around board edges
                new_x = (position.x + velocity.dx) % board.width
                new_y = (position.y + velocity.dy) % board.height

            position.x = new_x
            position.y = new_y

            # Reset interpolation alpha to 0.0 for smooth animation from old to new position
            if hasattr(snake, "interpolation"):
                snake.interpolation.alpha = 0.0
