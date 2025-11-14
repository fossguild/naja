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

"""SnakeRenderSystem - handles rendering of snake entities with interpolation.

This system follows ECS Single Responsibility Principle by handling ONLY
snake rendering with smooth interpolation effects.
"""

import pygame
from ecs.systems.base_system import BaseSystem
from ecs.world import World
from ecs.entities.entity import EntityType
from ecs.components.position import Position
from ecs.components.snake_body import SnakeBody
from ecs.components.interpolation import Interpolation
from ecs.components.color_scheme import ColorScheme
from core.rendering.pygame_surface_renderer import RenderEnqueue
from core.types.color import Color
from game import constants


class SnakeRenderSystem(BaseSystem):
    """System responsible for rendering snake entities with smooth interpolation.

    Responsibilities (following SRP):
    - Render snake head with interpolation
    - Render snake body segments with interpolation
    - Handle wraparound portal effects
    - Use colors from Palette component or ColorScheme fallback

    This system queries entities by components (Position, SnakeBody, Interpolation)
    rather than by entity type, following ECS data-driven principles.
    """

    def __init__(self, renderer: RenderEnqueue):
        """Initialize the SnakeRenderSystem.

        Args:
            renderer: RenderEnqueue view to queue draw commands
        """
        self._renderer = renderer

    def _get_color_scheme(self, world: World) -> ColorScheme:
        """Get ColorScheme component from world entities.

        Args:
            world: Game world

        Returns:
            ColorScheme component, or default if not found
        """
        color_entities = world.registry.query_by_component("color_scheme")

        if color_entities:
            entity = next(iter(color_entities.values()))
            return entity.color_scheme

        return ColorScheme()

    def draw_snake(
        self,
        world: World,
        position: Position,
        body: SnakeBody,
        interpolation: Interpolation,
        renderable=None,
    ) -> None:
        """Draw the snake with smooth interpolation.

        Args:
            world: Game world
            position: Head position component
            body: Snake body component
            interpolation: Interpolation component for smooth movement
            renderable: Optional renderable component for head color
        """
        if not body.alive:
            return

        cell_size = world.board.cell_size
        grid_width = world.board.width * cell_size
        grid_height = world.board.height * cell_size

        # Get colors from renderable or use constants as fallback
        if renderable and hasattr(renderable, "color"):
            head_color = renderable.color.to_tuple()
            # Use secondary color for tail if available, otherwise derive from head or use constant
            if hasattr(renderable, "secondary_color") and renderable.secondary_color:
                tail_color = renderable.secondary_color.to_tuple()
            else:
                tail_color = Color.from_hex(constants.TAIL_COLOR).to_tuple()
        else:
            head_color = Color.from_hex(constants.HEAD_COLOR).to_tuple()
            tail_color = Color.from_hex(constants.TAIL_COLOR).to_tuple()

        # Draw tail segments with interpolation
        self._draw_snake_tail(
            body,
            interpolation,
            position,
            cell_size,
            grid_width,
            grid_height,
            tail_color,
        )

        # Draw head with interpolation
        self._draw_snake_head(
            position, interpolation, cell_size, grid_width, grid_height, head_color
        )

    def _draw_snake_head(
        self,
        position: Position,
        interpolation: Interpolation,
        cell_size: int,
        grid_width: int,
        grid_height: int,
        color: tuple,
    ) -> None:
        """Draw the snake head with smooth interpolation.

        Args:
            position: Head position component
            interpolation: Interpolation component
            cell_size: Size of grid cells
            grid_width: Total grid width in pixels
            grid_height: Total grid height in pixels
            color: Head color as (r, g, b) tuple
        """
        # Calculate smooth interpolated position
        draw_x, draw_y = self._calculate_interpolated_position(
            position.x * cell_size,
            position.y * cell_size,
            position.prev_x * cell_size,
            position.prev_y * cell_size,
            interpolation.alpha,
            interpolation.wrapped_axis,
            cell_size,
            grid_width,
            grid_height,
        )

        # Draw head rectangle at interpolated position
        rect = pygame.Rect(int(draw_x), int(draw_y), cell_size, cell_size)
        self._renderer.draw_rect(color, rect, 0)

        # Draw wraparound duplicate for smooth portal effect
        if interpolation.wrapped_axis != "none":
            self._draw_wraparound_duplicate(
                draw_x,
                draw_y,
                cell_size,
                grid_width,
                grid_height,
                interpolation.wrapped_axis,
                color,
            )

    def _draw_snake_tail(
        self,
        body: SnakeBody,
        interpolation: Interpolation,
        head_position: Position,
        cell_size: int,
        grid_width: int,
        grid_height: int,
        color: tuple,
    ) -> None:
        """Draw the snake tail with smooth interpolation for each segment.

        Args:
            body: Snake body component
            interpolation: Interpolation component
            head_position: Current head position
            cell_size: Size of grid cells
            grid_width: Total grid width in pixels
            grid_height: Total grid height in pixels
            color: Tail color as (r, g, b) tuple
        """
        if not body.segments:
            return

        # Draw each tail segment with interpolation
        for segment in body.segments:
            draw_x, draw_y = self._calculate_interpolated_position(
                segment.x * cell_size,
                segment.y * cell_size,
                segment.prev_x * cell_size,
                segment.prev_y * cell_size,
                interpolation.alpha,
                interpolation.wrapped_axis,
                cell_size,
                grid_width,
                grid_height,
            )

            segment_rect = pygame.Rect(
                int(draw_x),
                int(draw_y),
                cell_size,
                cell_size,
            )
            self._renderer.draw_rect(color, segment_rect, 0)

            # Draw wraparound duplicate
            if interpolation.wrapped_axis != "none":
                self._draw_wraparound_duplicate(
                    draw_x,
                    draw_y,
                    cell_size,
                    grid_width,
                    grid_height,
                    interpolation.wrapped_axis,
                    color,
                )

    def _calculate_interpolated_position(
        self,
        current_x: int,
        current_y: int,
        prev_x: int,
        prev_y: int,
        alpha: float,
        wrapped_axis: str,
        cell_size: int,
        grid_width: int,
        grid_height: int,
    ) -> tuple[float, float]:
        """Calculate interpolated position with edge wrapping support.

        Args:
            current_x: Current x position
            current_y: Current y position
            prev_x: Previous x position
            prev_y: Previous y position
            alpha: Interpolation factor [0.0, 1.0]
            wrapped_axis: Which axis wrapped ("none", "x", "y", "both")
            cell_size: Size of grid cells
            grid_width: Total grid width in pixels
            grid_height: Total grid height in pixels

        Returns:
            Tuple of (interpolated_x, interpolated_y)
        """
        draw_x = prev_x + (current_x - prev_x) * alpha
        draw_y = prev_y + (current_y - prev_y) * alpha

        # Handle wrapping on x-axis
        if wrapped_axis in ("x", "both"):
            if abs(current_x - prev_x) > grid_width / 2:
                if current_x < prev_x:
                    draw_x = prev_x + alpha * cell_size
                else:
                    draw_x = prev_x - alpha * cell_size

        # Handle wrapping on y-axis
        if wrapped_axis in ("y", "both"):
            if abs(current_y - prev_y) > grid_height / 2:
                if current_y < prev_y:
                    draw_y = prev_y + alpha * cell_size
                else:
                    draw_y = prev_y - alpha * cell_size

        # Wrap coordinates to stay within grid bounds
        draw_x = draw_x % grid_width
        draw_y = draw_y % grid_height

        return (draw_x, draw_y)

    def _draw_wraparound_duplicate(
        self,
        draw_x: float,
        draw_y: float,
        cell_size: int,
        grid_width: int,
        grid_height: int,
        wrapped_axis: str,
        color: tuple,
    ) -> None:
        """Draw duplicate of segment on opposite edge for smooth wraparound.

        Args:
            draw_x: Current X position
            draw_y: Current Y position
            cell_size: Size of grid cells
            grid_width: Total grid width in pixels
            grid_height: Total grid height in pixels
            wrapped_axis: Which axis wrapped
            color: Segment color
        """
        dup_x = draw_x
        dup_y = draw_y

        if wrapped_axis in ("x", "both"):
            if draw_x >= grid_width - cell_size:
                dup_x = draw_x - grid_width
            elif draw_x < cell_size:
                dup_x = draw_x + grid_width

        if wrapped_axis in ("y", "both"):
            if draw_y >= grid_height - cell_size:
                dup_y = draw_y - grid_height
            elif draw_y < cell_size:
                dup_y = draw_y + grid_height

        # Only draw duplicate if position actually changed
        if dup_x != draw_x or dup_y != draw_y:
            dup_rect = pygame.Rect(int(dup_x), int(dup_y), cell_size, cell_size)
            self._renderer.draw_rect(color, dup_rect, 0)

    def update(self, world: World) -> None:
        """Update method required by BaseSystem.

        Renders all snake entities with smooth interpolation.
        Queries entities by components rather than type.

        Args:
            world: Game world to render
        """
        # Query snakes by required components (ECS data-driven approach)
        snakes = world.registry.query_by_type_and_components(
            EntityType.SNAKE, "position", "body", "interpolation"
        )

        for _, snake in snakes.items():
            # Get components
            position = snake.position
            body = snake.body
            interpolation = snake.interpolation
            renderable = getattr(snake, "renderable", None)

            # Render snake
            self.draw_snake(world, position, body, interpolation, renderable)
