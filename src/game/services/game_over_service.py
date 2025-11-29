#!/usr/bin/env python3
#
#   Copyright (c) 2023, Monaco F. J. <monaco@usp.br>
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

"""Game over service.

This service is responsible for handling the game over logic when the snake dies.
"""

from typing import Optional

from ecs.world import World
from ecs.entities.entity import EntityType
from game.services.audio_service import AudioService
from ecs.systems.scoring import ScoringSystem


class GameOverService:
    """Service to centralize game over logic."""

    def __init__(
        self,
        audio_service: Optional[AudioService] = None,
        scoring_system: Optional[ScoringSystem] = None,
    ):
        self._audio_service = audio_service
        self._scoring_system = scoring_system

    def handle_death(self, world: World, reason: str) -> None:
        """Handle snake death.

        1. Calculate and save final score.
        2. Mark snake as dead.
        3. Play death SFX/Music.
        4. Update GameState.

        Args:
            world: ECS world
            reason: Death reason message (e.g., "wall", "self-bite", "obstacle")
        """

        # Get current score and save to scoreboard via scoring system
        current_score = 0
        if self._scoring_system:
            current_score = self._scoring_system.get_current_score(world)
            # Delegate scoreboard management to scoring system
            self._scoring_system.save_score_to_scoreboard(world)

        # kill the snake
        snake = self._get_snake_entity(world)
        if snake and hasattr(snake, "body"):
            snake.body.alive = False

        # play death sound and music
        if self._audio_service:
            self._audio_service.play_sound("assets/sound/gameover.wav")
            self._audio_service.play_music("assets/sound/death_song.mp3")

        # update game state
        game_state = self._get_game_state(world)
        if game_state:
            game_state.game_over = True
            game_state.death_reason = reason
            game_state.next_scene = "game_over"
            game_state.final_score = current_score  # Store score in GameState

        print(f"☠️ DEATH CAUSE: {reason}")

    def _get_snake_entity(self, world: World):
        """Helper to find snake entity."""
        snakes = world.registry.query_by_type(EntityType.SNAKE)
        for _, snake in snakes.items():
            return snake
        return None

    def _get_game_state(self, world: World):
        """Helper to find game state entity."""
        game_state_entities = world.registry.query_by_component("game_state")
        if game_state_entities:
            entity = next(iter(game_state_entities.values()))
            if hasattr(entity, "game_state"):
                return entity.game_state
        return None
