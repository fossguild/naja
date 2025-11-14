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

"""Component data tests."""

from ecs.components import Position, Renderable, Interpolation, Grid
from core.types.color import Color


class TestVisualComponents:
    """Test visual components implementation."""

    def test_position_component(self):
        """Test Position component creation and fields."""
        pos = Position(x=10, y=20, prev_x=5, prev_y=15)

        assert pos.x == 10
        assert pos.y == 20
        assert pos.prev_x == 5
        assert pos.prev_y == 15

        # Test default values
        pos_default = Position(x=0, y=0)
        assert pos_default.prev_x == 0
        assert pos_default.prev_y == 0

    def test_renderable_component(self):
        """Test Renderable component creation and fields."""
        color = Color(255, 0, 0)
        renderable = Renderable(shape="circle", color=color, size=30)

        assert renderable.shape == "circle"
        assert renderable.color == color
        assert renderable.size == 30

        # Test default size
        renderable_default = Renderable(shape="square", color=color)
        assert renderable_default.size == 20

    def test_interpolation_component(self):
        """Test Interpolation component creation and fields."""
        interp = Interpolation(alpha=0.5, wrapped_axis="x")

        assert interp.alpha == 0.5
        assert interp.wrapped_axis == "x"

        # Test default values
        interp_default = Interpolation()
        assert interp_default.alpha == 0.0
        assert interp_default.wrapped_axis == "none"

    def test_grid_component(self):
        """Test Grid component creation and fields."""
        grid = Grid(width=20, height=15, cell_size=32, offset=(10, 10))

        assert grid.width == 20
        assert grid.height == 15
        assert grid.cell_size == 32
        assert grid.offset == (10, 10)

        # Test default offset
        grid_default = Grid(width=10, height=10, cell_size=16)
        assert grid_default.offset == (0, 0)
