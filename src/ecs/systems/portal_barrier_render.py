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

"""Portal Barrier Render System - renders both entry and exit blocks of portal barriers."""

import pygame
from ecs.systems.base_system import BaseSystem
from ecs.world import World
from ecs.entities.entity import EntityType
from core.rendering.pygame_surface_renderer import RenderEnqueue


class PortalBarrierRenderSystem(BaseSystem):
    """System responsible for rendering portal barrier entry and exit blocks.

    This system renders both the entry block (via the standard EntityRenderSystem)
    and the exit block for visual clarity.

    Responsibilities:
    - Render portal barrier exit blocks
    - Use same color as entry blocks for visual consistency
    """

    def __init__(self, renderer: RenderEnqueue):
        """Initialize the PortalBarrierRenderSystem.

        Args:
            renderer: RenderEnqueue view to queue draw commands
        """
        self._renderer = renderer

    def get_board_offset(self) -> tuple[int, int]:
        """Get the offset for the game board from screen edge.

        Returns:
            Tuple of (x_offset, y_offset) in pixels
        """
        # Get screen dimensions
        surface = pygame.display.get_surface()
        if not surface:
            return (0, 0)

        # Top offset for UI elements - use fixed 45px to ensure board fits completely
        top_offset = 45

        return (0, top_offset)

    def update(self, world: World) -> None:
        """Update method to render portal barrier blocks.

        Args:
            world: Game world to render
        """
        # Query all portal barriers
        portal_barriers = world.registry.query_by_type(EntityType.PORTAL_BARRIER)

        # Get cell size from board
        cell_size = world.board.cell_size

        # Get board offset
        offset_x, offset_y = self.get_board_offset()

        # Render both blocks for each portal barrier
        for _, portal_barrier in portal_barriers.items():
            if not hasattr(portal_barrier, "portal_barrier") or not hasattr(
                portal_barrier, "renderable"
            ):
                continue

            barrier = portal_barrier.portal_barrier
            renderable = portal_barrier.renderable

            # Skip if not visible
            if not renderable.visible:
                continue

            # Get color tuple
            color = renderable.get_color_tuple()

            # Render block1
            pixel_x1 = offset_x + barrier.block1_x * cell_size
            pixel_y1 = offset_y + barrier.block1_y * cell_size
            rect1 = pygame.Rect(pixel_x1, pixel_y1, cell_size, cell_size)
            self._renderer.draw_rect(color, rect1, 0)

            # Render block2
            pixel_x2 = offset_x + barrier.block2_x * cell_size
            pixel_y2 = offset_y + barrier.block2_y * cell_size
            rect2 = pygame.Rect(pixel_x2, pixel_y2, cell_size, cell_size)
            self._renderer.draw_rect(color, rect2, 0)
