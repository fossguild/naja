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

"""Speed boost system for Speed Boost Mode.

Manages the lifecycle of speed boosts, including timing and deactivation.
"""

from __future__ import annotations

from ecs.systems.base_system import BaseSystem
from ecs.world import World
from ecs.entities.entity import EntityType


class SpeedBoostSystem(BaseSystem):
    """System for managing speed boost timing in Speed Boost Mode.

    Reads: GameState (speed_boost_mode_enabled), SpeedBoost component
    Writes: SpeedBoost (remaining_time, active)

    Responsibilities:
    - Decrement boost timer each frame
    - Deactivate boost when timer reaches zero
    - Only process when Speed Boost Mode is enabled
    """

    def update(self, world: World) -> None:
        """Update speed boost timers for all snakes.

        Args:
            world: ECS world instance
        """
        # Check if Speed Boost Mode is enabled
        game_state_entities = world.registry.query_by_component("game_state")
        if not game_state_entities:
            return

        game_state_entity = next(iter(game_state_entities.values()))
        if not hasattr(game_state_entity, "game_state"):
            return

        game_state = game_state_entity.game_state

        # Only process if speed boost mode is enabled
        if not game_state.speed_boost_mode_enabled:
            return

        # Get delta time in seconds
        dt_seconds = world.dt_ms / 1000.0

        # Get all snakes with speed_boost component
        snakes = world.registry.query_by_type(EntityType.SNAKE)

        for _, snake in snakes.items():
            # Skip snakes without speed_boost component
            if not hasattr(snake, "speed_boost") or snake.speed_boost is None:
                continue

            speed_boost = snake.speed_boost

            # Process only active boosts
            if speed_boost.active:
                # Decrement timer
                speed_boost.remaining_time -= dt_seconds

                # Deactivate if timer expired
                if speed_boost.remaining_time <= 0:
                    speed_boost.deactivate()
