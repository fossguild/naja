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

"""UIRenderSystem - handles rendering of basic HUD elements.

This system follows ECS Single Responsibility Principle by handling ONLY
basic HUD element rendering (score, speed bar, music indicator).
"""

import pygame
from ecs.systems.base_system import BaseSystem
from ecs.world import World
from ecs.entities.entity import EntityType
from core.rendering.pygame_surface_renderer import RenderEnqueue
from core.types.color import Color
from game import constants


class UIRenderSystem(BaseSystem):
    """System responsible for rendering basic HUD elements.

    Responsibilities:
    - Render score counter
    - Render speed bar
    - Render music indicator

    NOT responsible for:
    - Overlays (use OverlayRenderSystem)
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
        """Draw score with apple icon in top-left corner.

        Args:
            world: Game world to query score
            surface_width: Width of the surface
            surface_height: Height of the surface
        """
        # query score component from world
        score_entities = world.registry.query_by_component("score")
        if not score_entities:
            return

        # get first score entity
        score_entity = list(score_entities.values())[0]
        if not hasattr(score_entity, "score"):
            return

        current_score = score_entity.score.current

        try:
            # load apple icon - smaller size
            icon_size = int(surface_width / 35)
            padding = int(surface_width * 0.015)

            try:
                apple_icon = pygame.image.load("assets/sprites/tabler_apple-filled.png")
                apple_icon = pygame.transform.scale(apple_icon, (icon_size, icon_size))
            except Exception:
                apple_icon = None

            # font for score number - smaller size
            font_size = int(surface_width / 30)
            font_path = "assets/font/GetVoIP-Grotesque.ttf"

            try:
                score_font = pygame.font.Font(font_path, font_size)
            except Exception:
                score_font = pygame.font.Font(None, font_size)

            # get color from constants
            score_color = Color.from_hex(constants.SCORE_COLOR).to_tuple()

            # render score text
            score_text = score_font.render(str(current_score), True, score_color)

            # calculate vertical center of border area (top 8% of screen)
            border_height = int(surface_height * 0.08)
            center_y = border_height // 2

            # position in top-left corner, vertically centered
            if apple_icon:
                icon_y = center_y - icon_size // 2
                self._renderer.blit(apple_icon, (padding, icon_y))
                score_rect = score_text.get_rect()
                score_rect.midleft = (padding + icon_size + 10, center_y)
            else:
                score_rect = score_text.get_rect()
                score_rect.midleft = (padding, center_y)

            # blit score text
            self._renderer.blit(score_text, score_rect)

        except Exception:
            # silently fail if icon loading or rendering fails
            pass

    def draw_speed_bar(
        self, world: World, surface_width: int, surface_height: int
    ) -> None:
        """Draw speed bar with lightning icon in top-center.

        Args:
            world: World containing entities
            surface_width: Width of the surface
            surface_height: Height of the surface
        """
        if not self._settings:
            return

        # get speed settings
        initial_speed = self._settings.get("initial_speed")
        max_speed = self._settings.get("max_speed")
        if initial_speed is None or max_speed is None:
            return

        min_speed = float(initial_speed)
        max_speed = float(max_speed)

        # get current speed from snake
        snakes = world.registry.query_by_type(EntityType.SNAKE)
        current_speed = min_speed
        for _, snake in snakes.items():
            if hasattr(snake, "velocity"):
                current_speed = snake.velocity.speed
                break

        # geometry - smaller sizes
        icon_size = int(surface_width / 40)
        bar_width = int(surface_width * 0.15)
        bar_height = int(surface_height * 0.012)

        # colors - bar changes from green (slow) to red (fast)
        if max_speed > min_speed:
            ratio = (current_speed - min_speed) / (max_speed - min_speed)
        else:
            ratio = 0.0
        ratio = max(0.0, min(ratio, 1.0))

        bar_color = (255, 255, 255)  # white fill
        border_color = (100, 100, 100)  # gray border
        text_color = Color.from_hex(constants.SCORE_COLOR).to_tuple()

        # load lightning icon - smaller
        try:
            bolt_icon = pygame.image.load("assets/sprites/tabler_bolt-filled.png")
            bolt_icon = pygame.transform.scale(bolt_icon, (icon_size, icon_size))
        except Exception:
            bolt_icon = None

        # center position horizontally and vertically
        center_x = surface_width // 2
        border_height = int(surface_height * 0.08)
        center_y = border_height // 2

        # draw lightning icon, vertically centered
        if bolt_icon:
            icon_x = center_x - bar_width // 2 - icon_size - 5
            icon_y = center_y - icon_size // 2
            self._renderer.blit(bolt_icon, (icon_x, icon_y))

        # draw speed bar, vertically centered
        bar_x = center_x - bar_width // 2
        bar_y = center_y - bar_height // 2

        # create temporary surface for the speed bar with border
        bar_surface = pygame.Surface((bar_width, bar_height))
        bar_surface.fill(border_color)

        # draw filled portion
        filled_width = int(bar_width * ratio)
        if filled_width > 0:
            filled_rect = pygame.Rect(0, 0, filled_width, bar_height)
            pygame.draw.rect(bar_surface, bar_color, filled_rect)

        # blit bar to screen
        self._renderer.blit(bar_surface, (bar_x, bar_y))

        # draw "Speed: X.X" text to the right of the bar - smaller font
        label_text = f"Speed: {current_speed:.1f}"
        font_size = int(surface_width / 60)
        font_path = "assets/font/GetVoIP-Grotesque.ttf"

        try:
            font = pygame.font.Font(font_path, font_size)
        except Exception:
            font = pygame.font.Font(None, font_size)

        label_surf = font.render(label_text, True, text_color)
        label_rect = label_surf.get_rect()
        label_rect.midleft = (bar_x + bar_width + 5, center_y)

        # blit label
        self._renderer.blit(label_surf, label_rect)

    def draw_high_score(
        self, world: World, surface_width: int, surface_height: int
    ) -> None:
        """Draw high score with trophy icon in top-right corner.

        Args:
            world: Game world to query score
            surface_width: Width of the surface
            surface_height: Height of the surface
        """
        # query score component from world
        score_entities = world.registry.query_by_component("score")
        if not score_entities:
            return

        # get first score entity
        score_entity = list(score_entities.values())[0]
        if not hasattr(score_entity, "score"):
            return

        high_score = score_entity.score.high_score

        try:
            # load trophy icon - smaller size
            icon_size = int(surface_width / 35)
            padding = int(surface_width * 0.015)

            try:
                trophy_icon = pygame.image.load(
                    "assets/sprites/tabler_trophy-filled.png"
                )
                trophy_icon = pygame.transform.scale(
                    trophy_icon, (icon_size, icon_size)
                )
            except Exception:
                trophy_icon = None

            # font for high score number - smaller size
            font_size = int(surface_width / 30)
            font_path = "assets/font/GetVoIP-Grotesque.ttf"

            try:
                score_font = pygame.font.Font(font_path, font_size)
            except Exception:
                score_font = pygame.font.Font(None, font_size)

            # get color from constants
            score_color = Color.from_hex(constants.SCORE_COLOR).to_tuple()

            # render high score text
            score_text = score_font.render(str(high_score), True, score_color)
            score_rect = score_text.get_rect()

            # calculate vertical center of border area
            border_height = int(surface_height * 0.08)
            center_y = border_height // 2

            # position with more space from right edge for return button
            # Leave space for return button (icon_size + padding * 2)
            right_margin = padding + icon_size + padding * 2
            score_rect.midright = (surface_width - right_margin, center_y)

            if trophy_icon:
                icon_x = score_rect.left - icon_size - 10
                icon_y = center_y - icon_size // 2
                self._renderer.blit(trophy_icon, (icon_x, icon_y))

            # blit score text
            self._renderer.blit(score_text, score_rect)

        except Exception:
            # silently fail if icon loading or rendering fails
            pass

    def draw_return_button(self, surface_width: int, surface_height: int) -> None:
        """Draw return button with arrow icon in top-right corner (far right).

        Args:
            surface_width: Width of the surface
            surface_height: Height of the surface
        """
        try:
            # load arrow icon - smaller size
            icon_size = int(surface_width / 35)
            padding = int(surface_width * 0.015)

            try:
                arrow_icon = pygame.image.load(
                    "assets/sprites/tabler_arrow-back-up.png"
                )
                arrow_icon = pygame.transform.scale(arrow_icon, (icon_size, icon_size))
            except Exception:
                arrow_icon = None

            # calculate vertical center of border area
            border_height = int(surface_height * 0.08)
            center_y = border_height // 2

            # position in top-right corner (far right), vertically centered
            if arrow_icon:
                icon_x = surface_width - padding - icon_size
                icon_y = center_y - icon_size // 2
                self._renderer.blit(arrow_icon, (icon_x, icon_y))

        except Exception:
            # silently fail if icon loading fails
            pass

    def draw_hunger_bar(
        self, world: World, surface_width: int, surface_height: int
    ) -> None:
        """Draw a horizontal bar showing the snake's current hunger/time left.

        Args:
            world: World containing entities
            surface_width: Width of the surface
            surface_height: Height of the surface
        """
        # geometry similar to speed bar
        padding_x = int(surface_width * 0.02)
        padding_y = int(surface_height * 0.02)
        bar_width = int(surface_width * 0.25)
        bar_height = int(surface_height * 0.02)
        gap = 6

        # query hunger component
        hunger_entities = world.registry.query_by_component("hunger")
        if not hunger_entities:
            return

        hunger_entity = list(hunger_entities.values())[0]
        if not hasattr(hunger_entity, "hunger"):
            return

        hunger = hunger_entity.hunger
        ratio = 0.0
        try:
            if hunger.max_time > 0:
                ratio = max(0.0, min(hunger.current_time / hunger.max_time, 1.0))
        except Exception:
            ratio = 0.0

        # colors
        bar_color = Color.from_hex(constants.HUNGER_COLOR).to_tuple()
        border_color = Color.from_hex(constants.GRID_COLOR).to_tuple()
        text_color = Color.from_hex(constants.MESSAGE_COLOR).to_tuple()

        # position: draw below speed bar (a bit lower)
        bar_x = padding_x
        # push down by speed bar height + gap + label area
        bar_y = (
            padding_y
            + int(surface_height * 0.02)
            + gap
            + int(surface_height * 0.02)
            + gap
        )

        # create temporary surface for the hunger bar
        bar_surface = pygame.Surface((bar_width, bar_height))
        bar_surface.fill(border_color)

        # draw filled portion
        filled_width = int(bar_width * ratio)
        if filled_width > 0:
            filled_rect = pygame.Rect(0, 0, filled_width, bar_height)
            pygame.draw.rect(bar_surface, bar_color, filled_rect)

        # blit bar to screen
        self._renderer.blit(bar_surface, (bar_x, bar_y))

        # draw text label below
        label_text = f"Hunger: {hunger.current_time:.1f}s"
        font_size = int(surface_width / 50)
        font_path = "assets/font/GetVoIP-Grotesque.ttf"

        try:
            font = pygame.font.Font(font_path, font_size)
        except Exception:
            font = pygame.font.Font(None, font_size)

        label_surf = font.render(label_text, True, text_color)
        label_rect = label_surf.get_rect()
        label_rect.midtop = (bar_x + bar_width // 2, bar_y + bar_height + gap)

        # blit label
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
            # define dimensions
            padding_x = int(surface_width * 0.02)
            padding_y = int(surface_height * 0.02)
            icon_size = int(surface_width / 25)
            gap = 4

            # load speaker sprites
            try:
                if music_on:
                    sprite = pygame.image.load("assets/sprites/speaker-on.png")
                else:
                    sprite = pygame.image.load("assets/sprites/speaker-muted.png")
            except Exception:
                sprite = None

            # render hint text - white when on, dim grid color when off
            hint_color = (
                Color.from_hex(constants.SCORE_COLOR).to_tuple()
                if music_on
                else Color.from_hex(constants.GRID_COLOR).to_tuple()
            )
            hint_text = "[N]"
            hint_font_size = int(surface_width / 50)
            font_path = "assets/font/GetVoIP-Grotesque.ttf"

            try:
                hint_font = pygame.font.Font(font_path, hint_font_size)
            except Exception:
                hint_font = pygame.font.Font(None, hint_font_size)

            hint_surf = hint_font.render(hint_text, True, hint_color)
            hint_rect = hint_surf.get_rect()

            # calculate total widget height
            total_widget_height = icon_size + gap + hint_rect.height

            # calculate positions (bottom-right corner)
            icon_x = surface_width - padding_x - icon_size
            icon_y = surface_height - padding_y - total_widget_height

            # scale and draw sprite
            if sprite is not None:
                scaled_sprite = pygame.transform.scale(sprite, (icon_size, icon_size))
                self._renderer.blit(scaled_sprite, (icon_x, icon_y))

            # position and draw text hint below the icon
            hint_rect.centerx = icon_x + icon_size // 2
            hint_rect.top = icon_y + icon_size + gap
            self._renderer.blit(hint_surf, hint_rect)

        except Exception:
            # silently fail if sprite loading or rendering fails
            pass

    def update(self, world: World) -> None:
        """Update method required by BaseSystem.

        Renders basic HUD elements on top of the game world.

        Args:
            world: Game world to render
        """
        # get surface dimensions
        surface = pygame.display.get_surface()
        if not surface:
            return

        surface_width = surface.get_width()
        surface_height = surface.get_height()

        # draw new border UI elements
        self.draw_score(
            world, surface_width, surface_height
        )  # top-left with apple icon
        self.draw_high_score(
            world, surface_width, surface_height
        )  # top-right with trophy icon
        self.draw_speed_bar(
            world, surface_width, surface_height
        )  # top-center with lightning icon
        self.draw_return_button(
            surface_width, surface_height
        )  # top-right (far right) with arrow icon

        # draw hunger bar only if enabled in settings (keep below for now)
        if self._settings and bool(self._settings.get("enable_hunger")):
            self.draw_hunger_bar(world, surface_width, surface_height)

        # draw music indicator (keep in bottom-right)
        if self._settings:
            music_on = self._settings.get("background_music")
            self.draw_music_indicator(surface_width, surface_height, music_on)
