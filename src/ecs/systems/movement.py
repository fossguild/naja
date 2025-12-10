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

            # Check if Cheese mode is enabled (for gaps/holes feature)
            game_state_entities = world.registry.query_by_component("game_state")
            cheese_mode = False
            if game_state_entities:
                entity = next(iter(game_state_entities.values()))
                if hasattr(entity, "game_state"):
                    cheese_mode = entity.game_state.cheese_mode_enabled

            # ===== UNIVERSAL STATIONARY SEGMENTS =====
            # All modes now use stationary segment placement for sprite support
            # Segments are placed at head's previous position and DON'T MOVE
            # This is better for sprites because each segment has a fixed grid cell

            # Track move history (used for cheese mode gaps)
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

            # Determine if we should add a segment this frame
            if cheese_mode:
                # Cheese mode: Only add segment every OTHER move (creates gaps)
                should_add_segment = move_number % 2 == 0
            else:
                # All other modes: Add segment every move (no gaps)
                should_add_segment = True

            # Handle growth differently based on mode
            if cheese_mode:
                # CHEESE MODE: pending_growth controls when to NOT remove tail
                # +2 pending_growth per apple = 2 frames of not removing tail
                # But since we only add segments every other frame, this = 1 new solid segment
                is_growing = hasattr(body, "pending_growth") and body.pending_growth > 0
                if is_growing:
                    body.pending_growth -= 1
            else:
                # CLASSIC/OTHER MODES: pending_growth adds to size immediately
                if hasattr(body, "pending_growth") and body.pending_growth > 0:
                    body.size += 1
                    body.pending_growth -= 1
                is_growing = False  # Classic mode doesn't use is_growing flag

            # Calculate desired number of segments (size - 1 because head isn't a segment)
            desired_segments = max(0, body.size - 1)

            if should_add_segment:
                # Create new STATIONARY segment at head's previous position
                new_segment = Position(
                    x=position.prev_x,
                    y=position.prev_y,
                    prev_x=position.prev_x,
                    prev_y=position.prev_y,
                )
                body.segments.insert(0, new_segment)

            # Trim/grow segments based on mode
            if cheese_mode:
                # Cheese mode: remove oldest segment unless growing
                if not is_growing and should_add_segment:
                    if len(body.segments) > 0:
                        body.segments.pop()
                # Update size to reflect actual segments
                body.size = len(body.segments) + 1
            else:
                # Classic mode: trim excess segments to match desired size
                while len(body.segments) > desired_segments:
                    body.segments.pop()

            # Reset interpolation alpha to 0.0 for smooth animation from old to new position
            if hasattr(snake, "interpolation"):
                snake.interpolation.alpha = 0.0
