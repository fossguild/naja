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

"""Tests for Portal Barrier Mode."""

from ecs.board import Board
from ecs.world import World
from ecs.entities.entity import EntityType
from ecs.prefabs.portal_barrier import create_portal_barrier
from ecs.systems.collision import CollisionSystem
from ecs.prefabs.snake import create_snake


class TestPortalBarrier:
    """Test portal barrier functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.board = Board(width=20, height=20, cell_size=20)
        self.world = World(self.board)

    def test_create_portal_barrier(self):
        """Test creating a portal barrier entity."""
        barrier_id = create_portal_barrier(
            self.world,
            block1_x=5,
            block1_y=5,
            block2_x=6,
            block2_y=5,
            grid_size=20,
        )

        assert barrier_id is not None

        # Verify the barrier was created
        portal_barriers = self.world.registry.query_by_type(EntityType.PORTAL_BARRIER)
        assert len(portal_barriers) == 1

        # Verify barrier properties
        _, barrier = next(iter(portal_barriers.items()))
        assert barrier.portal_barrier.block1_x == 5
        assert barrier.portal_barrier.block1_y == 5
        assert barrier.portal_barrier.block2_x == 6
        assert barrier.portal_barrier.block2_y == 5

    def test_portal_barrier_has_position_and_renderable(self):
        """Test that portal barrier has position and renderable components."""
        create_portal_barrier(
            self.world,
            block1_x=5,
            block1_y=5,
            block2_x=6,
            block2_y=5,
            grid_size=20,
        )

        portal_barriers = self.world.registry.query_by_type(EntityType.PORTAL_BARRIER)
        _, barrier = next(iter(portal_barriers.items()))

        # Check for position component
        assert hasattr(barrier, "position")
        assert barrier.position.x == 5
        assert barrier.position.y == 5

        # Check for renderable component
        assert hasattr(barrier, "renderable")
        assert barrier.renderable is not None

    def test_portal_barrier_bidirectional_teleportation_block1_to_block2(self):
        """Test snake teleportation from block1 to block2."""
        # Create snake at position (5, 5)
        snake = create_snake(
            self.world,
            head_x=5,
            head_y=5,
            length=3,
            grid_size=20,
        )

        # Create portal barrier with blocks at (6, 5) and (10, 5)
        create_portal_barrier(
            self.world,
            block1_x=6,
            block1_y=5,
            block2_x=10,
            block2_y=5,
            grid_size=20,
        )

        # Move snake to block1
        snake.position.x = 6
        snake.position.y = 5
        snake.position.prev_x = 5
        snake.position.prev_y = 5

        # Create collision system and check portal barrier
        collision_system = CollisionSystem()

        # Call portal barrier collision check
        collision_system._check_portal_barrier_collision(self.world)

        # Verify snake was teleported to block2
        assert snake.position.x == 10
        assert snake.position.y == 5

    def test_portal_barrier_bidirectional_teleportation_block2_to_block1(self):
        """Test snake teleportation from block2 to block1."""
        # Create snake at position (5, 5)
        snake = create_snake(
            self.world,
            head_x=5,
            head_y=5,
            length=3,
            grid_size=20,
        )

        # Create portal barrier with blocks at (6, 5) and (10, 5)
        create_portal_barrier(
            self.world,
            block1_x=6,
            block1_y=5,
            block2_x=10,
            block2_y=5,
            grid_size=20,
        )

        # Move snake to block2
        snake.position.x = 10
        snake.position.y = 5
        snake.position.prev_x = 9
        snake.position.prev_y = 5

        # Create collision system and check portal barrier
        collision_system = CollisionSystem()

        # Call portal barrier collision check
        collision_system._check_portal_barrier_collision(self.world)

        # Verify snake was teleported to block1
        assert snake.position.x == 6
        assert snake.position.y == 5

    def test_multiple_portal_barriers(self):
        """Test creating multiple portal barriers."""
        create_portal_barrier(
            self.world,
            block1_x=5,
            block1_y=5,
            block2_x=6,
            block2_y=5,
            grid_size=20,
        )

        create_portal_barrier(
            self.world,
            block1_x=10,
            block1_y=10,
            block2_x=11,
            block2_y=10,
            grid_size=20,
        )

        portal_barriers = self.world.registry.query_by_type(EntityType.PORTAL_BARRIER)
        assert len(portal_barriers) == 2

    def test_portal_barrier_with_custom_color(self):
        """Test creating a portal barrier with custom color."""
        create_portal_barrier(
            self.world,
            block1_x=5,
            block1_y=5,
            block2_x=6,
            block2_y=5,
            grid_size=20,
            color=(255, 0, 255),  # magenta
        )

        portal_barriers = self.world.registry.query_by_type(EntityType.PORTAL_BARRIER)
        _, barrier = next(iter(portal_barriers.items()))

        # Verify color (Note: Color objects need get_color_tuple method)
        color_tuple = barrier.renderable.get_color_tuple()
        assert color_tuple == (255, 0, 255)
