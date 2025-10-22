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
from src.ecs.systems.base_system import BaseSystem
from src.ecs.world import World
from src.ecs.components.position import Position
from src.ecs.components.renderable import Renderable
from src.core.rendering.pygame_surface_renderer import RenderEnqueue


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

        # Render all shapes as rectangles for now
        # (RenderEnqueue only has draw_rect and draw_line)
        rect = pygame.Rect(pixel_x, pixel_y, cell_size, cell_size)
        self._renderer.draw_rect(color, rect, 0)

    def update(self, world: World) -> None:
        """Update method required by BaseSystem.

        Renders all entities with Position + Renderable components.
        This is a pure ECS approach - query by components, not by type.

        NOTE: Excludes SNAKE entities as they have dedicated SnakeRenderSystem
        for proper interpolation and segment rendering.

        Args:
            world: Game world to render
        """
        from src.ecs.entities.entity import EntityType

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
