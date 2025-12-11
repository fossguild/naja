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
"""Lights Out timing system.

Keeps a simple on/off timer for the Lights Out game mode, toggling blackout
state and updating remaining time so UI/render systems can read it.
"""

from ecs.systems.base_system import BaseSystem


class LightsOutSystem(BaseSystem):
    """Toggle blackout on a fixed interval/duration.

    Uses GameState for enabled/active flags and LightsOutState for timing config.
    """

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

    def _refresh_from_settings(self, state) -> None:
        if not self._settings:
            return
        try:
            interval_val = self._settings.get("lights_out_interval")
            duration_val = self._settings.get("lights_out_duration")
            radius_val = self._settings.get("lights_out_radius")

            if interval_val is not None:
                state.interval = float(interval_val)
            if duration_val is not None:
                state.duration = float(duration_val)
            if radius_val is not None:
                state.radius = int(radius_val)
        except Exception:
            # ignore malformed values; keep current ones
            pass

    def update(self, world) -> None:
        game_state = self._get_game_state(world)
        lights_out_state = self._get_lights_out_state(world)

        if not game_state or not lights_out_state:
            return

        self._refresh_from_settings(lights_out_state)

        if not game_state.lights_out_enabled:
            # Ensure stable state when mode is inactive
            game_state.lights_out_active = False
            return

        dt_seconds = 0.0
        try:
            dt_seconds = float(world.dt_ms) / 1000.0
        except Exception:
            dt_seconds = 0.016

        # Choose the target countdown based on current state
        if game_state.lights_out_active:
            lights_out_state.timer -= dt_seconds
            if lights_out_state.timer <= 0:
                game_state.lights_out_active = False
                # start cooldown until next blackout
                lights_out_state.timer = max(lights_out_state.interval, 0.1)
        else:
            # cooldown running
            lights_out_state.timer -= dt_seconds
            if lights_out_state.timer <= 0:
                game_state.lights_out_active = True
                # start blackout duration
                lights_out_state.timer = max(lights_out_state.duration, 0.1)

        # Minimal runtime sanitization to ensure safe operation
        # enforce positive interval and duration
        if (
            not isinstance(lights_out_state.interval, (int, float))
            or lights_out_state.interval <= 0
        ):
            lights_out_state.interval = 12.0
        if (
            not isinstance(lights_out_state.duration, (int, float))
            or lights_out_state.duration <= 0
        ):
            lights_out_state.duration = 4.0
        # clamp radius to board bounds
        max_radius = max(1, min(world.board.width, world.board.height))
        if not isinstance(lights_out_state.radius, int):
            try:
                lights_out_state.radius = int(lights_out_state.radius)
            except Exception:
                lights_out_state.radius = 4
        if lights_out_state.radius < 1:
            lights_out_state.radius = 1
        if lights_out_state.radius > max_radius:
            lights_out_state.radius = max_radius
        # ensure timer is valid and non-negative
        if not isinstance(lights_out_state.timer, (int, float)):
            lights_out_state.timer = lights_out_state.interval
        if lights_out_state.timer < 0:
            lights_out_state.timer = 0.0
