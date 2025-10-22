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

"""Color scheme component for global game colors."""

from dataclasses import dataclass, field
from src.core.types.color import Color


@dataclass
class ColorScheme:
    """Component storing the game's color palette.

    This component follows ECS principles by storing only data.
    Rendering systems can query this component to get consistent
    colors across the game without hard-coding values.

    Attributes:
        arena: Background color
        grid: Grid line color
        snake_head: Snake head color
        snake_body: Snake body segment color
        apple: Apple/food color
        obstacle: Obstacle/wall color
    """

    arena: Color = field(default_factory=lambda: Color.from_hex("#202020"))
    grid: Color = field(default_factory=lambda: Color.from_hex("#3c3c3b"))
    snake_head: Color = field(default_factory=lambda: Color.from_hex("#00aa00"))
    snake_body: Color = field(default_factory=lambda: Color.from_hex("#00ff00"))
    apple: Color = field(default_factory=lambda: Color.from_hex("#aa0000"))
    obstacle: Color = field(default_factory=lambda: Color.from_hex("#666666"))

    def get_color(self, name: str) -> Color:
        """Get a color by name.

        Args:
            name: Color name (e.g., "arena", "snake_head")

        Returns:
            Color instance, or white if name not found
        """
        return getattr(self, name, Color(255, 255, 255))

    def set_color(self, name: str, color: Color) -> None:
        """Set a color by name.

        Args:
            name: Color name
            color: New Color instance
        """
        if hasattr(self, name):
            setattr(self, name, color)
