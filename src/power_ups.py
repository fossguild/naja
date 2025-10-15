#!/usr/bin/env python3
#
#   Copyright (c) 2023, Monaco F. J. <monaco@usp.br>
#
#   This file is part of KobraPy.
#
#   KobraPy is free software: you can redistribute it and/or modify
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

"""Power-ups system: registration, spawn, drawing, effects, and timers.

This module provides a registry-based architecture to easily add new power-ups.
Each power-up registers its own behavior (draw hooks and collection effect) and
its assets (e.g., sprite). The main game only calls generic functions here.

Quick start (adding a new power-up):
    1) Create a sprite at: assets/sprites/<your_name>.png
    2) Write a registration function similar to `_register_invincibility()`
       and call it inside `powerups_init(...)`.
    3) Optionally, implement:
         - on_collect(state, powerup): apply the effect when collected
         - draw_world(state, arena, powerup): draw the pickup on the grid
         - draw_overlay(state, arena, powerup): draw on top of snake while active
    4) Spawn it via:
         - powerups_spawn(state, "your_name")
       or add its name to `candidates` in `powerups_try_periodic_spawn(...)`.
"""

from __future__ import annotations

import pygame
import random
from typing import Callable, Dict, Optional, TypedDict
from src.entities import Apple

from src.constants import (
    INVINCIBILITY_DURATION_MS,
)

# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------


class PowerUp(TypedDict, total=False):
    """Runtime representation of a power-up placed on the arena."""

    type: str
    x: int
    y: int
    # Optional arbitrary properties (e.g., durations, magnitudes)
    duration_ms: int


class PowerUpSpec(TypedDict, total=False):
    """Static behavior/asset spec registered for a power-up type."""

    sprite: Optional[pygame.Surface]
    on_collect: Callable[[object, PowerUp], None]
    draw_world: Optional[Callable[[object, pygame.Surface, PowerUp], None]]
    draw_overlay: Optional[Callable[[object, pygame.Surface, PowerUp], None]]


# Global registry: type -> spec
_REGISTRY: Dict[str, PowerUpSpec] = {}


# ---------------------------------------------------------------------------
# Sprite helpers
# ---------------------------------------------------------------------------


def _load_sprite(path: str) -> Optional[pygame.Surface]:
    """Load a sprite from disk, returning None on failure (with warning)."""
    try:
        return pygame.image.load(path)
    except pygame.error as e:
        print(f"Warning: Could not load sprite '{path}': {e}")
        return None


# ---------------------------------------------------------------------------
# Public lifecycle API
# ---------------------------------------------------------------------------


def powerups_init(state) -> None:
    """Attach power-up runtime fields and register built-in power-ups.

    Fields created on state:
        state.powerups: list of placed PowerUp dicts
        state.invincible_until_ms: countdown marker for 'invincibility'
        state.powerups_next_try_ms: next time to attempt periodic spawn
    """
    state.powerups = []
    state.invincible_until_ms = 0
    state.powerups_next_try_ms = 0

    # Register built-in power-ups here:
    _register_invincibility()


def powerups_reset(state) -> None:
    """Clear placed power-ups (does not spawn anything)."""
    state.powerups = []


# ---------------------------------------------------------------------------
# Generic spawn/draw/collect pipeline
# ---------------------------------------------------------------------------


def powerups_spawn(state, type_name: str, **props) -> None:
    """Spawn a power-up of type `type_name` at a free cell.

    Avoids overlap with apples and with other power-ups. Uses Apple placement
    logic to guarantee a valid free grid cell.
    """
    if type_name not in _REGISTRY:
        print(f"Warning: power-up type '{type_name}' is not registered.")
        return

    temp = Apple(state.width, state.height, state.grid_size)
    temp.ensure_valid_position(state.snake, state.obstacles)

    # Avoid overlap with apples
    while any((temp.x == a.x and temp.y == a.y) for a in state.apples):
        temp.ensure_valid_position(state.snake, state.obstacles)

    # Avoid overlap with existing power-ups
    while any((temp.x == p["x"] and temp.y == p["y"]) for p in state.powerups):
        temp.ensure_valid_position(state.snake, state.obstacles)

    powerup: PowerUp = {"type": type_name, "x": temp.x, "y": temp.y}
    powerup.update(props)
    state.powerups.append(powerup)


def powerups_draw_all(state, arena: pygame.Surface) -> None:
    """Draw all power-ups currently placed on the arena."""
    if not getattr(state, "powerups", None):
        return

    for p in state.powerups:
        spec = _REGISTRY.get(p["type"])
        if not spec:
            # Fallback: simple outline
            pygame.draw.rect(
                arena,
                (200, 200, 200),
                pygame.Rect(p["x"], p["y"], state.grid_size, state.grid_size),
                2,
            )
            continue

        if spec.get("draw_world"):
            spec["draw_world"](state, arena, p)
        else:
            # Default draw using sprite (if any)
            sprite = spec.get("sprite")
            rect = pygame.Rect(p["x"], p["y"], state.grid_size, state.grid_size)
            if sprite:
                scaled = pygame.transform.scale(
                    sprite, (state.grid_size, state.grid_size)
                )
                arena.blit(scaled, rect)
            else:
                pygame.draw.rect(arena, (200, 200, 200), rect, 2)


def powerups_draw_overlay_on_head(state, arena: pygame.Surface) -> None:
    """Let each power-up draw an optional overlay on the snake's head."""
    if not getattr(state, "powerups", None):
        # Even if no pickups placed, effects may be active (e.g., timers)
        pass

    # Give every registered power-up a chance to draw its overlay
    for type_name, spec in _REGISTRY.items():
        overlay = spec.get("draw_overlay")
        if overlay:
            # Provide a lightweight placeholder PowerUp for overlay if needed
            overlay(state, arena, {"type": type_name})


def powerups_handle_collisions(state) -> None:
    """Apply effects of power-ups collected by the snake and remove them."""
    if not getattr(state, "powerups", None):
        return

    for p in list(state.powerups):
        if state.snake.head.x == p["x"] and state.snake.head.y == p["y"]:
            spec = _REGISTRY.get(p["type"])
            if spec and spec.get("on_collect"):
                spec["on_collect"](state, p)

            state.powerups.remove(p)
            # No immediate respawn here — periodic spawn handles future attempts
            break


def powerups_pause_begin(state) -> None:
    """Mark the moment we entered a paused state (to freeze timers)."""
    state._powerups_pause_start_ms = pygame.time.get_ticks()


def powerups_pause_end(state) -> None:
    """Shift timers by the paused duration so they don't elapse while paused."""
    start = getattr(state, "_powerups_pause_start_ms", None)
    if start is None:
        return
    delta = pygame.time.get_ticks() - start
    state.invincible_until_ms = getattr(state, "invincible_until_ms", 0) + delta
    state.powerups_next_try_ms = getattr(state, "powerups_next_try_ms", 0) + delta
    state._powerups_pause_start_ms = None


def powerups_death_guard(state, on_die: Callable[[], None]) -> Callable[[], None]:
    """Wrap the death callback to ignore death while invincible (or others in future)."""

    def _guard():
        # Extend this condition when adding defensive power-ups
        if pygame.time.get_ticks() < getattr(state, "invincible_until_ms", 0):
            return
        on_die()

    return _guard


# ---------------------------------------------------------------------------
# HUD helpers (timers/indicators)
# ---------------------------------------------------------------------------


def powerups_draw_timer(state, arena: pygame.Surface, assets) -> None:
    """Draw a bottom-left HUD slot for time-limited effects (invincibility)."""
    # Freeze the visual countdown while paused by using the pause-start timestamp
    if not getattr(state, "game_on", False):
        now = getattr(state, "_powerups_pause_start_ms", pygame.time.get_ticks())
    else:
        now = pygame.time.get_ticks()

    remaining_ms = getattr(state, "invincible_until_ms", 0) - now
    if remaining_ms <= 0:
        return

    secs = max(0, remaining_ms) / 1000.0
    text = assets.render_small(f"{secs:.1f}s", (255, 255, 255))

    # Layout: bottom-left with margin
    icon_size = max(16, int(state.grid_size * 0.9))
    gap = 6
    margin = max(8, int(min(state.width, state.height) * 0.02))
    x = margin
    y = state.height - margin - icon_size

    # Draw the icon for the most salient active effect (invincibility)
    spec = _REGISTRY.get("invincibility")
    sprite = spec.get("sprite") if spec else None
    icon_rect = pygame.Rect(x, y, icon_size, icon_size)
    if sprite:
        arena.blit(pygame.transform.scale(sprite, (icon_size, icon_size)), icon_rect)
    else:
        pygame.draw.rect(arena, (255, 255, 255), icon_rect, 2)

    text_rect = text.get_rect()
    text_rect.left = x + icon_size + gap
    text_rect.centery = icon_rect.centery
    arena.blit(text, text_rect)


# ---------------------------------------------------------------------------
# Periodic spawn scheduler
# ---------------------------------------------------------------------------


def powerups_try_periodic_spawn(
    state,
    interval_ms: int = 8000,
    chance: float = 0.35,
    candidates: Optional[list[str]] = None,
) -> None:
    """Attempt to spawn a power-up every `interval_ms` if none is present.

    Args:
        state: Game state
        interval_ms: Minimum milliseconds between spawn attempts
        chance: Probability [0..1] to actually spawn on an attempt
        candidates: Optional prioritized list of power-up type names to pick from

    Behavior:
        - Does nothing if a power-up is already on the arena.
        - Honors a per-state `powerups_next_try_ms` cooldown.
        - Picks the first registered candidate (or 'invincibility' by default).
    """
    # Only if there are NO pickups on the arena
    if getattr(state, "powerups", None) and len(state.powerups) > 0:
        return

    now = pygame.time.get_ticks()
    if now < getattr(state, "powerups_next_try_ms", 0):
        return

    # Schedule next attempt window regardless of success
    state.powerups_next_try_ms = now + int(interval_ms)

    if state.get_free_cells_count() <= 0:
        return

    if random.random() >= max(0.0, min(1.0, chance)):
        return

    # Choose a type to spawn
    if candidates is None:
        candidates = ["invincibility"]

    chosen = next((t for t in candidates if t in _REGISTRY), None)
    if not chosen:
        # Nothing registered from the provided list
        return

    powerups_spawn(state, chosen)


# ---------------------------------------------------------------------------
# Backward-compatible convenience wrappers (used by main)
# ---------------------------------------------------------------------------


def powerups_spawn_invincibility(state) -> None:
    """Compatibility wrapper to spawn 'invincibility' via the generic API."""
    powerups_spawn(state, "invincibility")


def powerups_maybe_spawn_invincibility(state, chance: float = 0.35) -> None:
    """Compatibility wrapper for a probabilistic spawn of 'invincibility'."""
    if random.random() < max(0.0, min(1.0, chance)):
        powerups_spawn_invincibility(state)


# ---------------------------------------------------------------------------
# Built-in power-up: invincibility
# ---------------------------------------------------------------------------


def _register_invincibility() -> None:
    """Register the 'invincibility' power-up in the global registry."""
    sprite = _load_sprite("assets/sprites/shield.png")

    def _on_collect(state, p: PowerUp) -> None:
        """Apply/extend invincibility on collection."""
        now = pygame.time.get_ticks()
        dur = int(p.get("duration_ms", INVINCIBILITY_DURATION_MS))
        state.invincible_until_ms = max(now, state.invincible_until_ms) + dur

    def _draw_world(state, arena: pygame.Surface, p: PowerUp) -> None:
        """Draw the pickup on the grid (sprite fallback to outline)."""
        rect = pygame.Rect(p["x"], p["y"], state.grid_size, state.grid_size)
        if sprite:
            arena.blit(
                pygame.transform.scale(sprite, (state.grid_size, state.grid_size)), rect
            )
        else:
            pygame.draw.rect(arena, (200, 200, 200), rect, 2)

    def _draw_overlay(state, arena: pygame.Surface, _p: PowerUp) -> None:
        """Draw the shield overlay over the snake head while active."""
        if pygame.time.get_ticks() >= getattr(state, "invincible_until_ms", 0):
            return
        if not sprite:
            return
        head_rect = pygame.Rect(
            round(state.snake.draw_x),
            round(state.snake.draw_y),
            state.grid_size,
            state.grid_size,
        )
        arena.blit(
            pygame.transform.scale(sprite, (state.grid_size, state.grid_size)),
            head_rect,
        )

    _REGISTRY["invincibility"] = PowerUpSpec(
        sprite=sprite,
        on_collect=_on_collect,
        draw_world=_draw_world,
        draw_overlay=_draw_overlay,
    )
