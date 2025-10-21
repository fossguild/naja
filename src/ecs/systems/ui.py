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

"""StaticUISystem - handles rendering of static UI overlays and HUD elements."""

import pygame
from src.ecs.systems.base_system import BaseSystem
from src.ecs.systems.assets import AssetsSystem
from src.ecs.world import World
from src.core.types.color import Color
from src.core.rendering.pygame_surface_renderer import RenderEnqueue


class StaticUISystem(BaseSystem):
    """System responsible for rendering static/non-interactive UI overlays.

    This system handles all static UI rendering including:
    - Score displays
    - Health bars / HUD elements
    - Pause overlays and game over screens (rendering only)
    - Control hints and instructions
    - Debug overlays
    - FPS counters

    This system does NOT handle user interaction or menu logic - it only
    renders UI elements. For interactive menus and dialogs, use MenuSystem.

    It uses AssetsSystem to access fonts and sprites for UI elements.

    This system receives a RenderEnqueue view that only allows queueing draw
    commands, preventing interference with the rendering pipeline.

    Public API provides domain-specific methods like render_title(),
    render_pause_overlay(), render_score(), etc.

    Attributes:
        renderer: The RenderEnqueue view to queue draw commands
        assets: Reference to the AssetsSystem for accessing fonts/sprites
    """

    def __init__(self, renderer: RenderEnqueue, assets: AssetsSystem):
        """Initialize the StaticUISystem.

        Args:
            renderer: RenderEnqueue view to queue draw commands (enqueue-only access)
            assets: AssetsSystem instance for accessing fonts and sprites
        """
        self._renderer = renderer
        self._assets = assets

        # TODO: In the future, UI colors should come from a config
        # or settings system, allowing runtime customization
        self._colors: dict[str, Color] = {
            "text": Color.from_hex("#ffffff"),  # Default text color
            "text_dim": Color.from_hex("#808080"),  # Dimmed text color
            "score": Color.from_hex("#ffffff"),  # Score text color
            "message": Color.from_hex("#808080"),  # Message text color
        }

    def set_color(self, name: str, color: Color) -> None:
        """Update a color in the color scheme.

        Args:
            name: Color name (e.g., "text", "score")
            color: New Color instance
        """
        self._colors[name] = color

    def get_color(self, name: str) -> Color:
        """Get a color from the color scheme.

        Args:
            name: Color name

        Returns:
            Color: Color instance
        """
        return self._colors.get(name, Color(255, 255, 255))

    def _draw_text(
        self,
        text: str,
        x: int,
        y: int,
        color: Color,
        size_name: str = "small",
        centered: bool = False,
        antialias: bool = True,
    ) -> None:
        """Draw text at the specified position (private method).

        Args:
            text: Text to draw
            x: X position in pixels
            y: Y position in pixels
            color: Text color (Color instance)
            size_name: Font size ("big" or "small")
            centered: Whether to center the text at (x, y)
            antialias: Whether to use antialiasing
        """
        font = self._assets.get_font(size_name)
        text_surface = font.render(text, antialias, color.to_tuple())

        if centered:
            rect = text_surface.get_rect(center=(x, y))
            self._renderer.blit(text_surface, rect)
        else:
            self._renderer.blit(text_surface, (x, y))

    def _draw_text_custom(
        self,
        text: str,
        x: int,
        y: int,
        color: Color,
        size_px: int,
        centered: bool = False,
        antialias: bool = True,
    ) -> None:
        """Draw text with custom font size (private method).

        Args:
            text: Text to draw
            x: X position in pixels
            y: Y position in pixels
            color: Text color (Color instance)
            size_px: Font size in pixels
            centered: Whether to center the text at (x, y)
            antialias: Whether to use antialiasing
        """
        font = self._assets.get_custom_font(size_px)
        text_surface = font.render(text, antialias, color.to_tuple())

        if centered:
            rect = text_surface.get_rect(center=(x, y))
            self._renderer.blit(text_surface, rect)
        else:
            self._renderer.blit(text_surface, (x, y))

    # Public domain-specific rendering methods

    def render_title(self, title: str) -> None:
        """Render a centered title at the top of the screen.

        Args:
            title: Title text to display
        """
        width, height = self._renderer.size
        self._draw_text_custom(
            title,
            width // 2,
            height // 10,
            self.get_color("text"),
            size_px=int(width / 12),
            centered=True,
        )

    def render_message(self, message: str, y_position: int = None) -> None:
        """Render a centered message.

        Args:
            message: Message text to display
            y_position: Y position (defaults to center of screen)
        """
        width, height = self._renderer.size
        y = y_position if y_position is not None else height // 2
        self._draw_text(
            message,
            width // 2,
            y,
            self.get_color("message"),
            size_name="small",
            centered=True,
        )

    def render_pause_overlay(self) -> None:
        """Render a semi-transparent pause overlay with text."""
        width, height = self._renderer.size

        # Create semi-transparent overlay
        overlay = pygame.Surface((width, height), pygame.SRCALPHA)
        overlay.fill((32, 32, 32, 180))  # Dark gray, semi-transparent
        self._renderer.blit(overlay, (0, 0))

        # Render "Paused" text
        self._draw_text(
            "Paused",
            width // 2,
            height // 2,
            self.get_color("message"),
            size_name="big",
            centered=True,
        )

        # Render instruction
        self._draw_text(
            "Press P to continue",
            width // 2,
            height * 2 // 3,
            self.get_color("message"),
            size_name="small",
            centered=True,
        )

    def render_score(self, score: int) -> None:
        """Render the current score in the top-left corner.

        Args:
            score: Current score value
        """
        width = self._renderer.width
        self._draw_text_custom(
            f"Score: {score}",
            int(width * 0.05),
            int(width * 0.03),
            self.get_color("score"),
            size_px=int(width / 30),
            centered=False,
        )

    def render_controls_hint(self, hint_text: str) -> None:
        """Render control hints at the bottom of the screen.

        Args:
            hint_text: Control instructions to display
        """
        width, height = self._renderer.size
        self._draw_text_custom(
            hint_text,
            width // 2,
            int(height * 0.95),
            self.get_color("text_dim"),
            size_px=int(width / 50),
            centered=True,
        )

    def render_centered_message(self, title: str, subtitle: str) -> None:
        """Render a centered message with title and subtitle (game over, etc.).

        Args:
            title: Main title text
            subtitle: Subtitle text below the title
        """
        width, height = self._renderer.size

        # Title
        self._draw_text_custom(
            title,
            width // 2,
            int(height / 2.6),
            self.get_color("message"),
            size_px=int(width / 8),
            centered=True,
        )

        # Subtitle
        self._draw_text_custom(
            subtitle,
            width // 2,
            int(height / 1.8),
            self.get_color("message"),
            size_px=int(width / 20),
            centered=True,
        )

    def update(self, world: World) -> None:
        """Update method required by BaseSystem.

        Renders default UI elements (title, controls hint) by queueing draw commands.
        Does NOT execute the commands or update the display - that's handled by the
        main rendering loop which has full renderer access.

        This should be called AFTER BoardRenderSystem.update() so UI appears on top.

        Args:
            world: Game world (unused currently, reserved for future UI state)
        """
        # Queue default UI elements
        self.render_title("Naja")
        self.render_controls_hint("Q=quit | R=refresh | F=fullscreen | P=pause")
