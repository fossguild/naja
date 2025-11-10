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

"""Hunger system for snake starvation mechanics.

This system manages the hunger countdown timer and handles death by starvation.
When hunger reaches 0, the snake dies and the game ends.
"""

from typing import Optional, Any

from src.ecs.systems.base_system import BaseSystem
from src.ecs.world import World
from src.ecs.entities.entity import EntityType


class HungerSystem(BaseSystem):
    """System for managing snake hunger and starvation.

    Reads: Hunger, SnakeBody
    Writes: Hunger (current_time), GameState (death on starvation)
    Queries: entities with Hunger component

    Responsibilities:
    - Decrement hunger counter each frame
    - Detect starvation (hunger reaches 0)
    - Handle starvation death (modify GameState, play sounds)
    - Allow external reset of hunger (called on apple eaten)

    Note: This system is responsible only for countdown and death detection.
    Hunger reset is triggered externally (e.g., by CollisionSystem on apple eaten).
    """

    def __init__(self, audio_service: Optional[Any] = None):
        """Initialize the HungerSystem.

        Args:
            audio_service: Optional audio service for playing death sounds
        """
        self._audio_service = audio_service

    def update(self, world: World) -> None:
        """Decrement hunger timer and check for starvation.

        Called every frame. Updates hunger countdown and detects death by starvation.

        Args:
            world: ECS world
        """
        # Find entities with hunger component
        hunger_entities = world.registry.query_by_component("hunger")

        for entity_id, entity in hunger_entities.items():
            if not hasattr(entity, "hunger"):
                continue

            hunger = entity.hunger

            # If max_time is zero or negative, hunger is disabled for this entity
            if not hunger.max_time or hunger.max_time <= 0:
                continue

            # Recalculate hunger max_time based on current snake velocity if possible
            # Formula: hunger max time = 50 / current_velocity -> shortens the time as the snake gets fasters
            snake = self._get_snake_entity(world)
            try:
                if snake and hasattr(snake, "velocity") and snake.velocity.speed > 0:
                    hunger.max_time = 50.0 / float(snake.velocity.speed)
            except Exception:
                # keep existing hunger.max_time on error
                pass

            # Ensure current_time does not exceed the (possibly updated) max
            if hunger.current_time > hunger.max_time:
                hunger.current_time = hunger.max_time

            # Decrement hunger by frame delta time (use world.dt_ms for accurate timing)
            delta_time = world.dt_ms / 1000.0
            hunger.current_time -= delta_time

            # Clamp to 0
            if hunger.current_time < 0:
                hunger.current_time = 0

            # Check for starvation
            if hunger.current_time <= 0:
                self._handle_starvation(world)

    def _get_hunger_entity(self, world: World):
        """Get the Hunger component from world.

        Args:
            world: ECS world

        Returns:
            Hunger component or None if not found
        """
        hunger_entities = world.registry.query_by_component("hunger")
        if hunger_entities:
            entity = next(iter(hunger_entities.values()))
            if hasattr(entity, "hunger"):
                return entity.hunger
        return None

    def _get_game_state(self, world: World):
        """Get the GameState component from world.

        Args:
            world: ECS world

        Returns:
            GameState component or None if not found
        """
        game_state_entities = world.registry.query_by_component("game_state")
        if game_state_entities:
            entity = next(iter(game_state_entities.values()))
            if hasattr(entity, "game_state"):
                return entity.game_state
        return None

    def reset_hunger(self, world: World) -> None:
        """Reset hunger timer to maximum.

        Called when apple is eaten.

        Args:
            world: ECS world
        """
        hunger = self._get_hunger_entity(world)
        if hunger:
            hunger.current_time = hunger.max_time

    def get_hunger_ratio(self, world: World) -> float:
        """Get hunger as a ratio (0.0 to 1.0).

        Used for rendering the hunger bar.

        Args:
            world: ECS world

        Returns:
            Hunger ratio (current_time / max_time), or 0.0 if no hunger entity
        """
        hunger = self._get_hunger_entity(world)
        if hunger:
            if hunger.max_time > 0:
                return hunger.current_time / hunger.max_time
            return 0.0
        return 0.0

    def get_hunger_time(self, world: World) -> float:
        """Get current hunger time in seconds.

        Args:
            world: ECS world

        Returns:
            Current hunger time in seconds, or 0.0 if no hunger entity
        """
        hunger = self._get_hunger_entity(world)
        if hunger:
            return hunger.current_time
        return 0.0

    def _get_snake_entity(self, world: World):
        """Get the snake entity from world.

        Args:
            world: ECS world

        Returns:
            Snake entity or None if not found
        """
        snakes = world.registry.query_by_type(EntityType.SNAKE)
        for _, snake in snakes.items():
            return snake
        return None

    def _handle_starvation(self, world: World) -> None:
        """Handle snake death by starvation.

        Modifies GameState component and plays death audio.

        Args:
            world: ECS world
        """
        # Kill the snake
        snake = self._get_snake_entity(world)
        if snake and hasattr(snake, "body"):
            snake.body.alive = False

        # Play death sound and music
        if self._audio_service:
            self._audio_service.play_sound("assets/sound/gameover.wav")
            self._audio_service.play_music("assets/sound/death_song.mp3")

        # Update game state
        game_state = self._get_game_state(world)
        if game_state:
            game_state.game_over = True
            game_state.death_reason = "starvation"
            game_state.next_scene = "game_over"

        print("☠️  DEATH CAUSE: Starvation")
