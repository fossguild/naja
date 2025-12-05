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

from typing import Optional, Callable

from ecs.systems.base_system import BaseSystem
from ecs.world import World
from ecs.entities.entity import EntityType
from ecs.components.position import Position
from ecs.components.velocity import Velocity
from ecs.components.snake_body import SnakeBody


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
        self._accumulated_time = 0.0  # accumulated time in milliseconds
        self._get_electric_walls = get_electric_walls

    def update(self, world: World) -> None:
        # time-based movement that respects snake speed
        dt_ms = world.dt_ms
        self._accumulated_time += dt_ms

        # Get snake speed to determine move interval
        snakes = world.registry.query_by_type_and_components(
            EntityType.SNAKE, "position", "velocity", "body"
        )

        if not snakes:
            return

        # Get first snake's speed
        _, first_snake = next(iter(snakes.items()))
        if hasattr(first_snake, "velocity") and hasattr(first_snake.velocity, "speed"):
            speed = first_snake.velocity.speed
        else:
            speed = 12.0  # default speed

        # Calculate how long one grid cell movement should take
        move_interval_ms = 1000.0 / speed

        # Only move when accumulated time reaches the move interval
        if self._accumulated_time < move_interval_ms:
            return

        # Reset accumulated time for next movement
        self._accumulated_time = 0.0

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

            # Check if game has started (wait for first input)
            game_state_entities = world.registry.query_by_component("game_state")
            if game_state_entities:
                entity = next(iter(game_state_entities.values()))
                if hasattr(entity, "game_state") and not entity.game_state.game_started:
                    continue  # Don't move until player makes first input

            # Process buffered direction FIRST (before zero velocity check)
            # This allows autoplay to start snake moving from zero velocity
            if hasattr(snake, "input_buffer") and snake.input_buffer.moves:
                next_dx, next_dy = snake.input_buffer.moves.pop(0)
                velocity.dx = next_dx
                velocity.dy = next_dy

            # Only move if velocity is non-zero
            if velocity.dx == 0 and velocity.dy == 0:
                continue

            # Store previous position for smooth interpolation
            position.prev_x = position.x
            position.prev_y = position.y

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

            # Check if Cheese mode is enabled
            game_state_entities = world.registry.query_by_component("game_state")
            cheese_mode = False
            if game_state_entities:
                entity = next(iter(game_state_entities.values()))
                if hasattr(entity, "game_state"):
                    cheese_mode = entity.game_state.cheese_mode_enabled

            if cheese_mode:
                # ===== CHEESE MODE: Stationary segments =====
                # Segments only appear every OTHER move
                # This creates gaps (holes) and the jumping effect

                # Track if this is an odd or even move using history length
                move_number = len(body.previous_head_positions)

                # Record this move in history
                body.previous_head_positions.insert(
                    0,
                    Position(
                        x=position.prev_x,
                        y=position.prev_y,
                        prev_x=position.prev_x,
                        prev_y=position.prev_y,
                    ),
                )

                # Only add a segment every OTHER move (on even move numbers)
                # move_number starts at 0, so: 0, 2, 4, 6... = even = add segment
                should_add_segment = move_number % 2 == 0

                # Handle growth
                is_growing = hasattr(body, "pending_growth") and body.pending_growth > 0
                if is_growing:
                    body.pending_growth -= 1
                    # Don't remove tail when growing

                if should_add_segment:
                    # Create new STATIONARY segment at head's previous position
                    new_segment = Position(
                        x=position.prev_x,
                        y=position.prev_y,
                        prev_x=position.prev_x,
                        prev_y=position.prev_y,
                    )
                    body.segments.insert(0, new_segment)

                    # Remove oldest segment UNLESS we're growing
                    if not is_growing:
                        if len(body.segments) > 0:
                            body.segments.pop()

                # Track actual size (head + segments)
                body.size = len(body.segments) + 1

            else:
                # ===== CLASSIC MODE: Segment-following logic =====
                # Keep original implementation for Classic and other modes

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
                    body.segments[0].x = position.prev_x  # Head's OLD position
                    body.segments[0].y = position.prev_y
                    body.segments[0].prev_x = old_x
                    body.segments[0].prev_y = old_y

                # Process pending growth (for Cheese mode +2 mechanic)
                # Transfer one pending growth to actual size per frame for smooth growth
                if hasattr(body, "pending_growth") and body.pending_growth > 0:
                    body.size += 1
                    body.pending_growth -= 1

                # Maintain correct number of segments based on body size
                desired_tail_len = max(0, body.size - 1)

                # Add or remove segments as needed
                if len(body.segments) > desired_tail_len:
                    # Snake shrunk - remove excess segments from the end
                    body.segments = body.segments[:desired_tail_len]
                elif len(body.segments) < desired_tail_len:
                    # Snake grew - add new segments at the end
                    if body.segments:
                        # Add segments at the last segment's PREVIOUS position
                        # This allows them to interpolate smoothly as they follow the tail
                        last_segment = body.segments[-1]
                        for _ in range(desired_tail_len - len(body.segments)):
                            # New segment starts at last segment's previous position
                            # and will interpolate to the last segment's current position
                            new_seg = Position(
                                x=last_segment.prev_x,  # Start at prev position
                                y=last_segment.prev_y,
                                prev_x=last_segment.prev_x,  # No interpolation on first frame
                                prev_y=last_segment.prev_y,
                            )
                            body.segments.append(new_seg)
                            # Update reference for next segment (if adding multiple)
                            last_segment = new_seg
                    else:
                        # First segment - create at head's position
                        new_seg = Position(
                            x=position.prev_x,
                            y=position.prev_y,
                            prev_x=position.prev_x,
                            prev_y=position.prev_y,
                        )
                        body.segments.append(new_seg)

            # Reset interpolation alpha to 0.0 for smooth animation from old to new position
            if hasattr(snake, "interpolation"):
                snake.interpolation.alpha = 0.0
