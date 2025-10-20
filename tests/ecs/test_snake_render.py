#!/usr/bin/env python3
#
#   Copyright (c) 2023, Monaco F. J. <monaco@usp.br>
#   Copyright (c) 2024, Felipe Diniz <lfelipediniz@usp.br>
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

"""Tests for snake rendering with interpolation."""

import pytest
from src.ecs.entities.snake import Snake
from src.ecs.components.position import Position
from src.ecs.components.velocity import Velocity
from src.ecs.components.snake_body import SnakeBody
from src.ecs.components.interpolation import Interpolation
from src.ecs.components.renderable import Renderable
from src.ecs.components.palette import Palette
from src.ecs.world import World
from src.ecs.board import Board
from src.ecs.systems.board_display import BoardRenderSystem
from src.core.types.color import Color


class MockRenderer:
    """Mock renderer for testing."""

    def __init__(self):
        self.drawn_rects = []
        self.drawn_lines = []
        self.fill_calls = []

    def fill(self, color):
        """Mock fill method."""
        self.fill_calls.append(color)

    def draw_rect(self, color, rect):
        """Mock draw_rect method."""
        self.drawn_rects.append((color, rect))

    def draw_line(self, color, start, end, width):
        """Mock draw_line method."""
        self.drawn_lines.append((color, start, end, width))


def test_snake_render_basic():
    """Test basic snake rendering without interpolation."""
    # Create a world with a board
    world = World()
    world.board = Board(width=20, height=20, cell_size=20)

    # Create a snake entity
    snake = Snake(
        id=1,
        position=Position(x=100, y=100, prev_x=100, prev_y=100),
        velocity=Velocity(dx=1, dy=0),
        body=SnakeBody(segments=[], size=1, alive=True),
        interpolation=Interpolation(alpha=0.0, wrapped_axis="none"),
        renderable=Renderable(shape="rect", color="green", size=20),
        palette=Palette(primary_color=(0, 255, 0), secondary_color=(0, 170, 0)),
    )

    # Register snake in world
    world.registry.register_entity(snake)

    # Create render system with mock renderer
    mock_renderer = MockRenderer()
    render_system = BoardRenderSystem(mock_renderer)

    # Render the snake
    render_system.draw_ecs_entities(world)

    # Check that the head was drawn (at least one rect)
    assert len(mock_renderer.drawn_rects) >= 1

    # Check that the head was drawn at the correct position
    head_drawn = False
    for color, rect in mock_renderer.drawn_rects:
        if rect.x == 100 and rect.y == 100:
            head_drawn = True
            break

    assert head_drawn, "Snake head was not drawn at expected position"


def test_snake_render_with_tail():
    """Test snake rendering with tail segments."""
    # Create a world with a board
    world = World()
    world.board = Board(width=20, height=20, cell_size=20)

    # Create a snake entity with tail segments
    snake = Snake(
        id=1,
        position=Position(x=100, y=100, prev_x=80, prev_y=100),
        velocity=Velocity(dx=1, dy=0),
        body=SnakeBody(
            segments=[
                Position(x=80, y=100, prev_x=60, prev_y=100),
                Position(x=60, y=100, prev_x=40, prev_y=100),
            ],
            size=3,
            alive=True,
        ),
        interpolation=Interpolation(alpha=0.0, wrapped_axis="none"),
        renderable=Renderable(shape="rect", color="green", size=20),
        palette=Palette(primary_color=(0, 255, 0), secondary_color=(0, 170, 0)),
    )

    # Register snake in world
    world.registry.register_entity(snake)

    # Create render system with mock renderer
    mock_renderer = MockRenderer()
    render_system = BoardRenderSystem(mock_renderer)

    # Render the snake
    render_system.draw_ecs_entities(world)

    # Check that head + tail segments were drawn (3 total)
    assert len(mock_renderer.drawn_rects) >= 3


def test_snake_render_with_interpolation():
    """Test snake rendering with smooth interpolation."""
    # Create a world with a board
    world = World()
    world.board = Board(width=20, height=20, cell_size=20)

    # Create a snake entity with interpolation
    snake = Snake(
        id=1,
        position=Position(x=100, y=100, prev_x=80, prev_y=100),
        velocity=Velocity(dx=1, dy=0),
        body=SnakeBody(segments=[], size=1, alive=True),
        interpolation=Interpolation(alpha=0.5, wrapped_axis="none"),  # 50% interpolated
        renderable=Renderable(shape="rect", color="green", size=20),
        palette=Palette(primary_color=(0, 255, 0), secondary_color=(0, 170, 0)),
    )

    # Register snake in world
    world.registry.register_entity(snake)

    # Create render system with mock renderer
    mock_renderer = MockRenderer()
    render_system = BoardRenderSystem(mock_renderer)

    # Render the snake
    render_system.draw_ecs_entities(world)

    # Check that the head was drawn
    assert len(mock_renderer.drawn_rects) >= 1

    # Check that head is drawn between prev and current position (interpolated)
    head_rect = mock_renderer.drawn_rects[-1][1]  # Last drawn rect should be head
    # With alpha=0.5, position should be halfway between 80 and 100 = 90
    assert 85 <= head_rect.x <= 95, f"Expected head x around 90, got {head_rect.x}"


def test_snake_render_with_wrapping():
    """Test snake rendering with edge wrapping."""
    # Create a world with a board
    world = World()
    world.board = Board(width=20, height=20, cell_size=20)

    # Create a snake that wraps around the edge
    # Position at x=380 (near right edge), prev at x=0 (left edge)
    # This simulates wrapping from right to left
    snake = Snake(
        id=1,
        position=Position(x=380, y=100, prev_x=0, prev_y=100),
        velocity=Velocity(dx=-1, dy=0),
        body=SnakeBody(segments=[], size=1, alive=True),
        interpolation=Interpolation(alpha=0.5, wrapped_axis="x"),  # Wrapped on x-axis
        renderable=Renderable(shape="rect", color="green", size=20),
        palette=Palette(primary_color=(0, 255, 0), secondary_color=(0, 170, 0)),
    )

    # Register snake in world
    world.registry.register_entity(snake)

    # Create render system with mock renderer
    mock_renderer = MockRenderer()
    render_system = BoardRenderSystem(mock_renderer)

    # Render the snake
    render_system.draw_ecs_entities(world)

    # Check that the head was drawn
    assert len(mock_renderer.drawn_rects) >= 1

    # With wrapping, the head should be drawn in the wrapped position
    # The interpolation should handle the wrap smoothly


def test_snake_dead_not_rendered():
    """Test that dead snake is not rendered."""
    # Create a world with a board
    world = World()
    world.board = Board(width=20, height=20, cell_size=20)

    # Create a dead snake entity
    snake = Snake(
        id=1,
        position=Position(x=100, y=100, prev_x=100, prev_y=100),
        velocity=Velocity(dx=1, dy=0),
        body=SnakeBody(segments=[], size=1, alive=False),  # Dead!
        interpolation=Interpolation(alpha=0.0, wrapped_axis="none"),
        renderable=Renderable(shape="rect", color="green", size=20),
        palette=Palette(primary_color=(0, 255, 0), secondary_color=(0, 170, 0)),
    )

    # Register snake in world
    world.registry.register_entity(snake)

    # Create render system with mock renderer
    mock_renderer = MockRenderer()
    render_system = BoardRenderSystem(mock_renderer)

    # Render the snake
    render_system.draw_ecs_entities(world)

    # Dead snake should not be drawn
    assert len(mock_renderer.drawn_rects) == 0


def test_calculate_interpolated_position_no_wrap():
    """Test interpolated position calculation without wrapping."""
    world = World()
    world.board = Board(width=20, height=20, cell_size=20)

    mock_renderer = MockRenderer()
    render_system = BoardRenderSystem(mock_renderer)

    # Test interpolation from (80, 100) to (100, 100) with alpha=0.5
    draw_x, draw_y = render_system._calculate_interpolated_position(
        current_x=100,
        current_y=100,
        prev_x=80,
        prev_y=100,
        alpha=0.5,
        wrapped_axis="none",
        cell_size=20,
        grid_width=400,
        grid_height=400,
    )

    # Should be halfway between 80 and 100
    assert abs(draw_x - 90) < 1.0
    assert abs(draw_y - 100) < 1.0


def test_calculate_interpolated_position_with_x_wrap():
    """Test interpolated position calculation with x-axis wrapping."""
    world = World()
    world.board = Board(width=20, height=20, cell_size=20)

    mock_renderer = MockRenderer()
    render_system = BoardRenderSystem(mock_renderer)

    # Test wrapping from right edge (380) to left edge (0) with alpha=0.5
    draw_x, draw_y = render_system._calculate_interpolated_position(
        current_x=0,
        current_y=100,
        prev_x=380,
        prev_y=100,
        alpha=0.5,
        wrapped_axis="x",
        cell_size=20,
        grid_width=400,
        grid_height=400,
    )

    # Should interpolate smoothly across the wrap
    # With wrapping, position should advance by cell_size * alpha
    # Expected: 380 + 20 * 0.5 = 390, then wrap to 390 % 400 = 390
    assert 385 <= draw_x <= 395 or 0 <= draw_x <= 10


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
