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

"""Lights Out system

This system is intentionally minimal: when the Lights Out mode is enabled it
enforces a constant vision radius around snake heads. The visual behaviour is
driven by the renderer using `lights_out_state.radius`.
"""

from ecs.systems.base_system import BaseSystem


class LightsOutSystem(BaseSystem):
    """Always-on Lights Out: constant vision radius around snake head."""

    def __init__(self, settings=None):
        self._settings = settings

    def _get_game_state(self, world):
        entities = world.registry.query_by_component("game_state")
        if not entities:
            return None
        entity = next(iter(entities.values()))
        return getattr(entity, "game_state", None)

    def _get_lights_out_state(self, world):
        entities = world.registry.query_by_component("lights_out_state")
        if not entities:
            return None
        entity = next(iter(entities.values()))
        return getattr(entity, "lights_out_state", None)

    def update(self, world) -> None:
        """Enforce always-on blackout and constant vision radius.
        The radius is set to 4 tiles by design. Defensive clamping prevents
        unrealistic values that could break rendering.
        """
        game_state = self._get_game_state(world)
        lights_out_state = self._get_lights_out_state(world)

        if not game_state or not lights_out_state:
            return

        # If the mode is not enabled, do nothing
        if not game_state.lights_out_enabled:
            return

        # Desired fixed radius in tiles
        desired_radius = 2.25

        # Defensive clamp against board size
        board_width = getattr(getattr(world, "board", None), "width", 1)
        board_height = getattr(getattr(world, "board", None), "height", 1)
        max_radius = max(1, min(board_width, board_height))

        radius = int(desired_radius)
        if radius < 1:
            radius = 1
        if radius > max_radius:
            radius = max_radius

        lights_out_state.radius = radius
