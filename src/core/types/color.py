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

"""Color dataclass for RGB color representation."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Color:
    """Immutable RGB color representation.

    Represents a color using red, green, and blue components.
    Each component must be in the range [0, 255].

    Attributes:
        r: Red component (0-255)
        g: Green component (0-255)
        b: Blue component (0-255)

    Example:
        >>> red = Color(255, 0, 0)
        >>> green = Color.from_hex("#00ff00")
        >>> blue = Color.from_rgb((0, 0, 255))
    """

    r: int
    g: int
    b: int

    def __post_init__(self):
        """Validate color components are in valid range."""
        if not (0 <= self.r <= 255):
            raise ValueError(f"Red component must be 0-255, got {self.r}")
        if not (0 <= self.g <= 255):
            raise ValueError(f"Green component must be 0-255, got {self.g}")
        if not (0 <= self.b <= 255):
            raise ValueError(f"Blue component must be 0-255, got {self.b}")

    @classmethod
    def from_hex(cls, hex_string: str) -> "Color":
        """Create a Color from a hex string.

        Args:
            hex_string: Hex color string (e.g., "#ff0000" or "ff0000")

        Returns:
            Color: New Color instance

        Raises:
            ValueError: If hex string is invalid

        Example:
            >>> Color.from_hex("#ff0000")
            Color(r=255, g=0, b=0)
        """
        # Remove '#' if present
        hex_string = hex_string.lstrip("#")

        if len(hex_string) != 6:
            raise ValueError(f"Hex string must be 6 characters, got '{hex_string}'")

        try:
            r = int(hex_string[0:2], 16)
            g = int(hex_string[2:4], 16)
            b = int(hex_string[4:6], 16)
            return cls(r, g, b)
        except ValueError as e:
            raise ValueError(f"Invalid hex string '{hex_string}': {e}") from e

    @classmethod
    def from_rgb(cls, rgb_tuple: tuple[int, int, int]) -> "Color":
        """Create a Color from an RGB tuple.

        Args:
            rgb_tuple: Tuple of (r, g, b) values

        Returns:
            Color: New Color instance

        Example:
            >>> Color.from_rgb((255, 0, 0))
            Color(r=255, g=0, b=0)
        """
        return cls(*rgb_tuple)

    def to_tuple(self) -> tuple[int, int, int]:
        """Convert color to RGB tuple.

        Returns:
            tuple[int, int, int]: RGB tuple (r, g, b)

        Example:
            >>> Color(255, 0, 0).to_tuple()
            (255, 0, 0)
        """
        return (self.r, self.g, self.b)

    def to_hex(self) -> str:
        """Convert color to hex string.

        Returns:
            str: Hex string with '#' prefix

        Example:
            >>> Color(255, 0, 0).to_hex()
            '#ff0000'
        """
        return f"#{self.r:02x}{self.g:02x}{self.b:02x}"

    def __str__(self) -> str:
        """String representation as hex.

        Returns:
            str: Hex color string
        """
        return self.to_hex()

    def __repr__(self) -> str:
        """Detailed representation.

        Returns:
            str: Constructor-style representation
        """
        return f"Color(r={self.r}, g={self.g}, b={self.b})"


# Common color constants
BLACK = Color(0, 0, 0)
WHITE = Color(255, 255, 255)
RED = Color(255, 0, 0)
GREEN = Color(0, 255, 0)
BLUE = Color(0, 0, 255)
YELLOW = Color(255, 255, 0)
CYAN = Color(0, 255, 255)
MAGENTA = Color(255, 0, 255)
GRAY = Color(128, 128, 128)
DARK_GRAY = Color(64, 64, 64)
LIGHT_GRAY = Color(192, 192, 192)
