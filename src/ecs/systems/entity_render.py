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

"""EntityRenderSystem - renders entities based on Position + Renderable components.

This system follows ECS principles by querying entities based on their
components rather than their type, making it fully data-driven.
"""

import pygame
from ecs.systems.base_system import BaseSystem
from ecs.world import World
from ecs.components.position import Position
from ecs.components.renderable import Renderable
from core.rendering.pygame_surface_renderer import RenderEnqueue


class EntityRenderSystem(BaseSystem):
    """System responsible for rendering generic entities.

    This system renders ANY entity that has both Position and Renderable
    components, making it fully generic and data-driven.

    Responsibilities (following SRP):
    - Render entities with Position + Renderable components
    - Handle different shapes (circle, square, rectangle)
    - Respect rendering layers
    - Handle visibility flag

    NOT responsible for:
    - Snake rendering (use SnakeRenderSystem for interpolation)
    - UI elements (use UI systems)
    - Board/grid (use BoardRenderSystem)
    """

    def __init__(self, renderer: RenderEnqueue):
        """Initialize the EntityRenderSystem.

        Args:
            renderer: RenderEnqueue view to queue draw commands
        """
        self._renderer = renderer

    def draw_entity(
        self, position: Position, renderable: Renderable, cell_size: int
    ) -> None:
        """Draw a single entity based on its components.

        Args:
            position: Position component
            renderable: Renderable component
            cell_size: Size of grid cells in pixels
        """
        # Skip if not visible
        if not renderable.visible:
            return

        # Calculate pixel position
        pixel_x = position.x * cell_size
        pixel_y = position.y * cell_size

        # Get color tuple
        color = renderable.get_color_tuple()

        # Render based on shape
        if renderable.shape == "circle":
            # For apples, draw realistic apple with stem and leaf
            self._draw_realistic_apple(pixel_x, pixel_y, cell_size, color)
        elif renderable.shape in ["square", "rectangle"]:
            # Draw as rectangle (existing behavior)
            rect = pygame.Rect(pixel_x, pixel_y, cell_size, cell_size)
            self._renderer.draw_rect(color, rect, 0)
        else:
            # Default fallback to rectangle for unknown shapes
            rect = pygame.Rect(pixel_x, pixel_y, cell_size, cell_size)
            self._renderer.draw_rect(color, rect, 0)

    def _draw_realistic_apple(
        self, pixel_x: int, pixel_y: int, cell_size: int, color: tuple[int, int, int]
    ) -> None:
        """Draw a realistic apple with elliptical body, stem and leaf.

        Args:
            pixel_x: X position in pixels
            pixel_y: Y position in pixels
            cell_size: Size of the cell
            color: RGB color of the apple
        """
        # Apple body - slightly flattened ellipse
        body_width = int(cell_size * 0.8)
        body_height = int(cell_size * 0.7)
        body_x = pixel_x + (cell_size - body_width) // 2
        body_y = pixel_y + int(cell_size * 0.15)

        # Draw apple body as ellipse using multiple circles for smooth appearance
        center_x = body_x + body_width // 2

        # Main body - draw filled ellipse approximation
        radius_x = body_width // 2
        radius_y = body_height // 2

        # Draw ellipse as multiple horizontal lines
        for y in range(body_height):
            dy = y - radius_y
            if radius_y != 0:
                # Ellipse equation: (x/rx)² + (y/ry)² = 1
                # Solve for x: x = rx * sqrt(1 - (y/ry)²)
                normalized_y = dy / radius_y
                if abs(normalized_y) <= 1:
                    half_width = int(
                        radius_x * (1 - normalized_y * normalized_y) ** 0.5
                    )
                    line_y = body_y + y
                    line_start = center_x - half_width
                    line_end = center_x + half_width
                    if half_width > 0:
                        self._renderer.draw_line(
                            color, (line_start, line_y), (line_end, line_y), 1
                        )

        # Apple stem (caule) - small brown rectangle
        stem_color = (101, 67, 33)  # Brown color
        stem_width = max(2, cell_size // 10)
        stem_height = max(3, cell_size // 6)
        stem_x = center_x - stem_width // 2
        stem_y = pixel_y + 2
        stem_rect = pygame.Rect(stem_x, stem_y, stem_width, stem_height)
        self._renderer.draw_rect(stem_color, stem_rect, 0)

        # Apple leaf (folha) - small green triangle-like shape
        leaf_color = (34, 139, 34)  # Forest green
        leaf_size = max(3, cell_size // 8)

        # Draw leaf as small lines forming a leaf shape
        leaf_x = stem_x + stem_width + 1
        leaf_y = stem_y + 1

        # Leaf outline - draw a small oval-like shape
        for i in range(leaf_size):
            y_offset = i
            if i < leaf_size // 2:
                # Upper half - expanding
                width = (i * 2) // 3 + 1
            else:
                # Lower half - contracting
                width = ((leaf_size - i) * 2) // 3 + 1

            for w in range(width):
                point_x = leaf_x + w
                point_y = leaf_y + y_offset
                # Draw individual pixels for leaf
                self._renderer.draw_line(
                    leaf_color, (point_x, point_y), (point_x, point_y), 1
                )

    def update(self, world: World) -> None:
        """Update method required by BaseSystem.

        Renders all entities with Position + Renderable components.
        This is a pure ECS approach - query by components, not by type.

        NOTE: Excludes SNAKE entities as they have dedicated SnakeRenderSystem
        for proper interpolation and segment rendering.

        Args:
            world: Game world to render
        """
        from ecs.entities.entity import EntityType

        # Query all entities with Position and Renderable components
        # This is the ECS way - data-driven, not type-driven
        entities = world.registry.query_by_component("position", "renderable")

        # Get cell size from board
        cell_size = world.board.cell_size

        # Sort entities by rendering layer (optional, for proper layering)
        sorted_entities = sorted(
            entities.items(), key=lambda item: getattr(item[1].renderable, "layer", 0)
        )

        # Render each entity (except snakes - they have dedicated system)
        for entity_id, entity in sorted_entities:
            # Skip snakes - they are rendered by SnakeRenderSystem
            if hasattr(entity, "get_type") and entity.get_type() == EntityType.SNAKE:
                continue

            position = entity.position
            renderable = entity.renderable

            self.draw_entity(position, renderable, cell_size)
