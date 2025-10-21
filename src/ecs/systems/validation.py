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

"""Validation system for debugging and integrity checks.

This system validates game state and detects anomalies for debugging purposes.
It does not fix problems, only reports them via logging.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Tuple, Set

from src.ecs.systems.base_system import BaseSystem
from src.ecs.world import World
from src.ecs.entities.entity import EntityType

# configure logger for validation warnings
logger = logging.getLogger("ValidationSystem")


class ValidationSystem(BaseSystem):
    """System for validating game state and detecting anomalies.

    Reads: All entities (Position, Edible, SnakeBody, ObstacleTag, etc.)
    Writes: None (read-only validation)
    Queries: All entities for validation

    Responsibilities:
    - Verify exactly one apple exists (or configured amount)
    - Verify snake position is within board bounds
    - Verify no invalid entity overlap (snake on obstacle, etc.)
    - Log warnings for detected anomalies
    - Track validation statistics for debugging

    Note: This is a debugging aid. It does not modify game state,
    only reports problems via Python logging.
    """

    def __init__(
        self,
        enabled: bool = True,
        expected_apple_count: int = 1,
        log_level: int = logging.WARNING,
    ):
        """Initialize the ValidationSystem.

        Args:
            enabled: Whether validation is active
            expected_apple_count: Expected number of apples in game
            log_level: Logging level for validation messages
        """
        self._enabled = enabled
        self._expected_apple_count = expected_apple_count
        self._validation_count = 0
        self._anomaly_count = 0

        # configure logger
        logger.setLevel(log_level)
        if not logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(
                logging.Formatter("[%(name)s] %(levelname)s: %(message)s")
            )
            logger.addHandler(handler)

    def update(self, world: World) -> None:
        """Validate game state and log anomalies.

        This method is called every tick when enabled.
        It performs all validation checks and logs warnings.

        Args:
            world: ECS world containing entities and components
        """
        if not self._enabled:
            return

        self._validation_count += 1
        anomalies_found = False

        # run all validation checks
        if not self.validate_apple_count(world):
            anomalies_found = True

        if not self.validate_snake_bounds(world):
            anomalies_found = True

        if not self.validate_entity_overlaps(world):
            anomalies_found = True

        # track anomaly count
        if anomalies_found:
            self._anomaly_count += 1

    def validate_apple_count(self, world: World) -> bool:
        """Verify that exactly the expected number of apples exist.

        Args:
            world: ECS world

        Returns:
            True if apple count is correct, False if anomaly detected
        """
        # count apples by querying entities with Edible component
        apple_count = 0
        registry = world.registry

        for entity_id in registry.query_by_component("edible"):
            entity = registry.get(entity_id)
            if entity and hasattr(entity, "edible"):
                apple_count += 1

        # also check by entity type
        apples_by_type = registry.query_by_type(EntityType.APPLE)
        type_count = len(apples_by_type)

        # verify counts match
        if apple_count != type_count:
            logger.warning(
                f"Apple count mismatch: {apple_count} by component, "
                f"{type_count} by type"
            )
            return False

        # verify expected count
        if apple_count != self._expected_apple_count:
            logger.warning(
                f"Unexpected apple count: found {apple_count}, "
                f"expected {self._expected_apple_count}"
            )
            return False

        return True

    def validate_snake_bounds(self, world: World) -> bool:
        """Verify snake head and body segments are within board bounds.

        Args:
            world: ECS world

        Returns:
            True if all snake parts in bounds, False if out of bounds
        """
        board = world.board
        registry = world.registry
        all_valid = True

        # get snake entities
        snakes = registry.query_by_type(EntityType.SNAKE)

        for snake_id, snake in snakes.items():
            # check snake head position
            if hasattr(snake, "position"):
                pos = snake.position

                if not self._is_position_in_bounds(pos.x, pos.y, board):
                    logger.warning(
                        f"Snake head out of bounds: ({pos.x}, {pos.y}), "
                        f"board: {board.width}x{board.height}"
                    )
                    all_valid = False

            # check snake body segments
            if hasattr(snake, "body") and hasattr(snake.body, "segments"):
                for i, segment in enumerate(snake.body.segments):
                    if not self._is_position_in_bounds(segment.x, segment.y, board):
                        logger.warning(
                            f"Snake body segment {i} out of bounds: "
                            f"({segment.x}, {segment.y}), "
                            f"board: {board.width}x{board.height}"
                        )
                        all_valid = False

        return all_valid

    def validate_entity_overlaps(self, world: World) -> bool:
        """Verify no invalid entity overlaps exist.

        Invalid overlaps:
        - Snake head on obstacle
        - Snake body on obstacle
        - Multiple entities at exact same position (suspicious)

        Args:
            world: ECS world

        Returns:
            True if no invalid overlaps, False if overlaps detected
        """
        registry = world.registry
        all_valid = True

        # get all entity positions
        position_map: Dict[Tuple[int, int], List[int]] = {}

        for entity_id in registry.query_by_component("position"):
            entity = registry.get(entity_id)
            if entity and hasattr(entity, "position"):
                pos = entity.position
                key = (pos.x, pos.y)
                if key not in position_map:
                    position_map[key] = []
                position_map[key].append(entity_id)

        # also add snake body segments to position map
        snakes = registry.query_by_type(EntityType.SNAKE)
        for snake_id, snake in snakes.items():
            if hasattr(snake, "body") and hasattr(snake.body, "segments"):
                for segment in snake.body.segments:
                    key = (segment.x, segment.y)
                    if key not in position_map:
                        position_map[key] = []
                    # use negative ID to indicate body segment
                    position_map[key].append(-(snake_id + 1))

        # check for overlaps
        for pos, entity_ids in position_map.items():
            if len(entity_ids) > 1:
                # check what types are overlapping
                overlap_types = self._get_entity_types_at_position(world, entity_ids)

                # check for invalid combinations
                if "snake" in overlap_types and "obstacle" in overlap_types:
                    logger.warning(f"Invalid overlap at {pos}: snake on obstacle")
                    all_valid = False

                # multiple entities at exact same position is suspicious
                if len(entity_ids) > 2:
                    logger.warning(
                        f"Multiple entities ({len(entity_ids)}) at same position {pos}: "
                        f"types={overlap_types}"
                    )
                    all_valid = False

        return all_valid

    def validate_all(self, world: World) -> bool:
        """Run all validation checks and return overall result.

        Args:
            world: ECS world

        Returns:
            True if all validations pass, False if any anomaly detected
        """
        apple_valid = self.validate_apple_count(world)
        bounds_valid = self.validate_snake_bounds(world)
        overlap_valid = self.validate_entity_overlaps(world)

        return apple_valid and bounds_valid and overlap_valid

    def set_enabled(self, enabled: bool) -> None:
        """Enable or disable validation checks.

        Args:
            enabled: Whether to enable validation
        """
        self._enabled = enabled

    def is_enabled(self) -> bool:
        """Check if validation is enabled.

        Returns:
            True if enabled, False otherwise
        """
        return self._enabled

    def set_expected_apple_count(self, count: int) -> None:
        """Update expected apple count.

        Args:
            count: Expected number of apples
        """
        self._expected_apple_count = count

    def get_expected_apple_count(self) -> int:
        """Get expected apple count.

        Returns:
            Expected number of apples
        """
        return self._expected_apple_count

    def get_validation_count(self) -> int:
        """Get total number of validation runs.

        Returns:
            Number of times validation has run
        """
        return self._validation_count

    def get_anomaly_count(self) -> int:
        """Get number of times anomalies were detected.

        Returns:
            Number of validation runs that found anomalies
        """
        return self._anomaly_count

    def reset_statistics(self) -> None:
        """Reset validation statistics."""
        self._validation_count = 0
        self._anomaly_count = 0

    def get_statistics(self) -> Dict[str, int]:
        """Get validation statistics.

        Returns:
            Dictionary with validation and anomaly counts
        """
        return {
            "validation_count": self._validation_count,
            "anomaly_count": self._anomaly_count,
        }

    @staticmethod
    def _is_position_in_bounds(x: int, y: int, board) -> bool:
        """Check if position is within board bounds.

        Args:
            x: X coordinate
            y: Y coordinate
            board: Game board

        Returns:
            True if in bounds, False otherwise
        """
        return 0 <= x < board.width and 0 <= y < board.height

    def _get_entity_types_at_position(
        self, world: World, entity_ids: List[int]
    ) -> Set[str]:
        """Get types of entities at a position.

        Args:
            world: ECS world
            entity_ids: List of entity IDs (negative for body segments)

        Returns:
            Set of entity type strings
        """
        types = set()
        registry = world.registry

        for entity_id in entity_ids:
            # negative ID indicates snake body segment
            if entity_id < 0:
                types.add("snake_body")
                types.add("snake")  # general snake type
                continue

            entity = registry.get(entity_id)
            if not entity:
                continue

            # check for specific components to determine type
            if hasattr(entity, "edible"):
                types.add("apple")
            if hasattr(entity, "tag") and hasattr(entity.tag, "__class__"):
                if entity.tag.__class__.__name__ == "ObstacleTag":
                    types.add("obstacle")
            if hasattr(entity, "body") and hasattr(entity.body, "segments"):
                types.add("snake")

        return types
