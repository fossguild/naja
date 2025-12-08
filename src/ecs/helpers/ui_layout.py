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

"""UI layout helper for calculating UI element positions and bounding boxes.

This module provides shared layout calculations used by both rendering
systems (for drawing) and input systems (for hit detection).
"""

import pygame


class UILayout:
    """Shared UI layout calculations for rendering and hit detection."""

    @staticmethod
    def get_return_button_rect(surface_width: int, surface_height: int) -> pygame.Rect:
        """Calculate bounding box for return button in top-right corner.

        Args:
            surface_width: Width of the surface
            surface_height: Height of the surface

        Returns:
            pygame.Rect representing the clickable area of the return button
        """
        # icon dimensions (same as UIRenderSystem)
        icon_size = int(surface_width / 35)
        padding = int(surface_width * 0.015)

        # vertical positioning in border area
        border_height = 45
        center_y = border_height // 2

        # position in top-right corner
        icon_x = surface_width - padding - icon_size
        icon_y = center_y - icon_size // 2

        return pygame.Rect(icon_x, icon_y, icon_size, icon_size)

    @staticmethod
    def get_music_button_rect(surface_width: int, surface_height: int) -> pygame.Rect:
        """Calculate bounding box for music indicator button in bottom-right corner.

        Args:
            surface_width: Width of the surface
            surface_height: Height of the surface

        Returns:
            pygame.Rect representing the clickable area of the music button
        """
        # dimensions (same as UIRenderSystem.draw_music_indicator)
        padding_x = int(surface_width * 0.02)
        padding_y = int(surface_height * 0.02)
        icon_size = int(surface_width / 25)
        gap = 4

        # approximate hint text height
        hint_font_size = int(surface_width / 50)
        hint_height = int(hint_font_size * 1.2)

        # calculate total widget height
        total_widget_height = icon_size + gap + hint_height

        # calculate icon position (bottom-right corner)
        icon_x = surface_width - padding_x - icon_size
        icon_y = surface_height - padding_y - total_widget_height

        return pygame.Rect(icon_x, icon_y, icon_size, icon_size)
