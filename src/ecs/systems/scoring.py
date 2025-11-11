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

"""Scoring system for tracking player score and high score.

This system handles score updates when apples are eaten.
It maintains current score and high score, preserving high score
across game resets and settings changes.
"""

from __future__ import annotations

from src.ecs.systems.base_system import BaseSystem
from src.ecs.systems.system_decorators import skip_when_paused
from src.ecs.world import World


@skip_when_paused
class ScoringSystem(BaseSystem):
    """System for managing score and high score.

    Reads: Edible (for points value), SnakeBody (for current length)
    Writes: Score (current and high_score)
    Queries: entities with Score component

    Responsibilities:
    - Update score when apples are eaten
    - Track high score across games
    - Update score based on snake length
    - Preserve high score across settings changes
    - Reset current score on game over

    Note: Score in Naja is based on snake length (tail size).
    Each apple eaten adds points based on Edible.points component.
    """

    def __init__(self):
        """Initialize the ScoringSystem."""
        pass

    def update(self, world: World) -> None:
        """Update method required by BaseSystem.

        This system is event-driven and doesn't perform periodic updates.
        Score updates are triggered explicitly through method calls.

        Args:
            world: Game world (unused in this system)
        """
        # Scoring is handled explicitly via event methods
        # No periodic behavior needed
        pass

    def on_apple_eaten(self, world: World, points: int) -> None:
        """Handle apple eaten event and update score.

        Args:
            world: ECS world
            points: Points to add to score
        """
        # find score entity (should be singleton)
        score_entities = world.registry.query_by_component("current")

        if not score_entities:
            # no score entity exists, cannot update
            return

        # get first score entity (singleton pattern)
        score_entity_id = list(score_entities.keys())[0]
        score_entity = world.registry.get(score_entity_id)

        if not hasattr(score_entity, "current") or not hasattr(
            score_entity, "high_score"
        ):
            return

        # update current score
        score_entity.current += points

        # update high score if current exceeds it
        if score_entity.current > score_entity.high_score:
            score_entity.high_score = score_entity.current

    def update_score_from_snake_length(
        self, world: World, snake_tail_length: int
    ) -> None:
        """Update score based on snake tail length.

        In Naja, score = tail length.

        Args:
            world: ECS world
            snake_tail_length: Current snake tail length
        """
        # find score entity
        score_entities = world.registry.query_by_component("current")

        if not score_entities:
            return

        score_entity_id = list(score_entities.keys())[0]
        score_entity = world.registry.get(score_entity_id)

        if not hasattr(score_entity, "current") or not hasattr(
            score_entity, "high_score"
        ):
            return

        # update current score to match snake length
        score_entity.current = snake_tail_length

        # update high score if current exceeds it
        if score_entity.current > score_entity.high_score:
            score_entity.high_score = score_entity.current

    def reset_current_score(self, world: World) -> None:
        """Reset current score to 0 while preserving high score.

        Called on game over or restart.

        Args:
            world: ECS world
        """
        # find score entity
        score_entities = world.registry.query_by_component("current")

        if not score_entities:
            return

        score_entity_id = list(score_entities.keys())[0]
        score_entity = world.registry.get(score_entity_id)

        if not hasattr(score_entity, "current"):
            return

        # reset current score to 0
        score_entity.current = 0

    def get_current_score(self, world: World) -> int:
        """Get current score.

        Args:
            world: ECS world

        Returns:
            Current score, or 0 if no score entity exists
        """
        score_entities = world.registry.query_by_component("current")

        if not score_entities:
            return 0

        score_entity_id = list(score_entities.keys())[0]
        score_entity = world.registry.get(score_entity_id)

        if hasattr(score_entity, "current"):
            return score_entity.current

        return 0

    def get_high_score(self, world: World) -> int:
        """Get high score.

        Args:
            world: ECS world

        Returns:
            High score, or 0 if no score entity exists
        """
        score_entities = world.registry.query_by_component("current")

        if not score_entities:
            return 0

        score_entity_id = list(score_entities.keys())[0]
        score_entity = world.registry.get(score_entity_id)

        if hasattr(score_entity, "high_score"):
            return score_entity.high_score

        return 0

    def set_high_score(self, world: World, high_score: int) -> None:
        """Set high score explicitly.

        Used for loading saved high scores or testing.

        Args:
            world: ECS world
            high_score: High score value to set
        """
        score_entities = world.registry.query_by_component("current")

        if not score_entities:
            return

        score_entity_id = list(score_entities.keys())[0]
        score_entity = world.registry.get(score_entity_id)

        if hasattr(score_entity, "high_score"):
            score_entity.high_score = high_score

    def get_scores(self, world: World) -> tuple[int, int]:
        """Get both current and high scores.

        Args:
            world: ECS world

        Returns:
            Tuple of (current_score, high_score)
        """
        score_entities = world.registry.query_by_component("current")

        if not score_entities:
            return (0, 0)

        score_entity_id = list(score_entities.keys())[0]
        score_entity = world.registry.get(score_entity_id)

        current = score_entity.current if hasattr(score_entity, "current") else 0
        high = score_entity.high_score if hasattr(score_entity, "high_score") else 0

        return (current, high)
