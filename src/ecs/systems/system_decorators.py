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

"""Reusable decorators for ECS system classes.

This module defines class-level decorators that modify or extend
the behavior of ECS systems in a consistent and readable way.
They are used to express runtime behavior declaratively, without
requiring manual configuration in scene logic.
"""


def skip_when_paused(cls):
    """Decorator that marks a system to be skipped when the game is paused.

    Sets a class attribute `skip_when_paused = True` so that
    the system can be conditionally skipped in the scene update loop.

    Args:
        cls: The system class being decorated.

    Returns:
        The same class with the `skip_when_paused` attribute set.
    """
    cls.skip_when_paused = True
    return cls
