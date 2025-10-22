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

"""UIRenderSystem - handles rendering of UI overlays (score, speed bar, music indicator).

This system follows ECS Single Responsibility Principle by handling ONLY
UI element rendering on top of the game world.
"""

import pygame
from src.ecs.systems.base_system import BaseSystem
from src.ecs.world import World
from src.ecs.entities.entity import EntityType
from src.core.rendering.pygame_surface_renderer import RenderEnqueue


class UIRenderSystem(BaseSystem):
    """System responsible for rendering UI overlays.

    Responsibilities (following SRP):
    - Render score counter
    - Render speed bar
    - Render music indicator
    - Render pause overlay (when paused)

    NOT responsible for:
    - Game world rendering (use BoardRenderSystem)
    - Entity rendering (use EntityRenderSystem, SnakeRenderSystem)
    """

    def __init__(self, renderer: RenderEnqueue, settings=None):
        """Initialize the UIRenderSystem.

        Args:
            renderer: RenderEnqueue view to queue draw commands
            settings: Optional GameSettings instance for accessing settings
        """
        self._renderer = renderer
        self._settings = settings

    def draw_score(self, world: World, surface_width: int, surface_height: int) -> None:
        """Draw score counter horizontally centered near the top, semi-transparent.

        Args:
            world: Game world to query score
            surface_width: Width of the surface
            surface_height: Height of the surface
        """
        # Query score component from world
        score_entities = world.registry.query_by_component("score")
        if not score_entities:
            return

        # Get first score entity
        score_entity = list(score_entities.values())[0]
        if not hasattr(score_entity, "score"):
            return

        current_score = score_entity.score.current

        try:
            # Large font size
            font_size = int(surface_width / 8)
            font_path = "assets/font/GetVoIP-Grotesque.ttf"

            try:
                score_font = pygame.font.Font(font_path, font_size)
            except Exception:
                score_font = pygame.font.Font(None, font_size)

            # Gray color
            score_color = (128, 128, 128)

            # Render score text
            score_text = score_font.render(str(current_score), True, score_color)

            # Make it translucent (~25% opaque)
            score_text.set_alpha(64)

            # Horizontal center; vertically near the top with margin
            top_margin = getattr(
                world.board, "cell_size", max(10, surface_height // 20)
            )
            score_rect = score_text.get_rect()
            score_rect.midtop = (surface_width // 2, top_margin)

            # Blit to main surface
            self._renderer.blit(score_text, score_rect)

        except Exception:
            # Silently fail if font loading or rendering fails
            pass

    def draw_speed_bar(
        self, world: World, surface_width: int, surface_height: int
    ) -> None:
        """Draw a horizontal bar showing the snake's current speed.

        Args:
            world: World containing entities
            surface_width: Width of the surface
            surface_height: Height of the surface
        """
        if not self._settings:
            return

        # Get speed settings
        initial_speed = self._settings.get("initial_speed")
        max_speed = self._settings.get("max_speed")
        if initial_speed is None or max_speed is None:
            return

        min_speed = float(initial_speed)
        max_speed = float(max_speed)

        # Get current speed from snake
        snakes = world.registry.query_by_type(EntityType.SNAKE)
        current_speed = min_speed
        for _, snake in snakes.items():
            if hasattr(snake, "velocity"):
                current_speed = snake.velocity.speed
                break

        # Geometry
        padding_x = int(surface_width * 0.02)
        padding_y = int(surface_height * 0.02)
        bar_width = int(surface_width * 0.25)
        bar_height = int(surface_height * 0.02)
        gap = 6

        # Colors - bar changes from green (slow) to red (fast)
        if max_speed > min_speed:
            ratio = (current_speed - min_speed) / (max_speed - min_speed)
        else:
            ratio = 0.0
        ratio = max(0.0, min(ratio, 1.0))
        bar_color = (
            int(255 * ratio),
            int(255 * (1 - ratio)),
            0,
        )
        border_color = (50, 50, 50)
        text_color = (200, 200, 200)

        # Bar position
        bar_x = padding_x
        bar_y = padding_y

        # Create temporary surface for the speed bar
        bar_surface = pygame.Surface((bar_width, bar_height))
        bar_surface.fill(border_color)

        # Draw filled portion
        filled_width = int(bar_width * ratio)
        if filled_width > 0:
            filled_rect = pygame.Rect(0, 0, filled_width, bar_height)
            pygame.draw.rect(bar_surface, bar_color, filled_rect)

        # Blit bar to screen
        self._renderer.blit(bar_surface, (bar_x, bar_y))

        # Draw text label below
        label_text = f"Speed: {current_speed:.1f}"
        font_size = int(surface_width / 50)
        font_path = "assets/font/GetVoIP-Grotesque.ttf"

        try:
            font = pygame.font.Font(font_path, font_size)
        except Exception:
            font = pygame.font.Font(None, font_size)

        label_surf = font.render(label_text, True, text_color)
        label_rect = label_surf.get_rect()
        label_rect.midtop = (bar_x + bar_width // 2, bar_y + bar_height + gap)

        # Blit label
        self._renderer.blit(label_surf, label_rect)

    def draw_music_indicator(
        self, surface_width: int, surface_height: int, music_on: bool
    ) -> None:
        """Draw music status indicator in the bottom-right corner.

        Args:
            surface_width: Width of the surface
            surface_height: Height of the surface
            music_on: Whether background music is currently enabled
        """
        try:
            # Define dimensions
            padding_x = int(surface_width * 0.02)
            padding_y = int(surface_height * 0.02)
            icon_size = int(surface_width / 25)
            gap = 4

            # Load speaker sprites
            try:
                if music_on:
                    sprite = pygame.image.load("assets/sprites/speaker-on.png")
                else:
                    sprite = pygame.image.load("assets/sprites/speaker-muted.png")
            except Exception:
                sprite = None

            # Render hint text
            hint_color = (255, 255, 255) if music_on else (60, 60, 59)
            hint_text = "[N]"
            hint_font_size = int(surface_width / 50)
            font_path = "assets/font/GetVoIP-Grotesque.ttf"

            try:
                hint_font = pygame.font.Font(font_path, hint_font_size)
            except Exception:
                hint_font = pygame.font.Font(None, hint_font_size)

            hint_surf = hint_font.render(hint_text, True, hint_color)
            hint_rect = hint_surf.get_rect()

            # Calculate total widget height
            total_widget_height = icon_size + gap + hint_rect.height

            # Calculate positions (bottom-right corner)
            icon_x = surface_width - padding_x - icon_size
            icon_y = surface_height - padding_y - total_widget_height

            # Scale and draw sprite
            if sprite is not None:
                scaled_sprite = pygame.transform.scale(sprite, (icon_size, icon_size))
                self._renderer.blit(scaled_sprite, (icon_x, icon_y))

            # Position and draw text hint below the icon
            hint_rect.centerx = icon_x + icon_size // 2
            hint_rect.top = icon_y + icon_size + gap
            self._renderer.blit(hint_surf, hint_rect)

        except Exception:
            # Silently fail if sprite loading or rendering fails
            pass

    def update(self, world: World) -> None:
        """Update method required by BaseSystem.

        Renders UI overlays on top of the game world.

        Args:
            world: Game world to render
        """
        # Get surface dimensions
        surface = pygame.display.get_surface()
        if not surface:
            return

        surface_width = surface.get_width()
        surface_height = surface.get_height()

        # Draw UI elements
        self.draw_score(world, surface_width, surface_height)
        self.draw_speed_bar(world, surface_width, surface_height)

        # Draw music indicator
        if self._settings:
            music_on = self._settings.get("background_music")
            self.draw_music_indicator(surface_width, surface_height, music_on)
