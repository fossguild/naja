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

"""SnakeRenderSystem - handles rendering of snake entities with interpolation.

This system follows ECS Single Responsibility Principle by handling ONLY
snake rendering with smooth interpolation effects.
"""

import pygame
from ecs.systems.base_system import BaseSystem
from ecs.world import World
from ecs.entities.entity import EntityType
from ecs.components.position import Position
from ecs.components.snake_body import SnakeBody
from ecs.components.interpolation import Interpolation
from ecs.components.color_scheme import ColorScheme
from core.rendering.pygame_surface_renderer import RenderEnqueue
from core.types.color import Color
from game import constants
from game.constants import get_rainbow_color

# Direction to rotation angle mapping (degrees)
# Base sprite orientation assumed to be facing RIGHT (0 degrees)
DIRECTION_TO_ROTATION = {
    (1, 0): 0,  # RIGHT - no rotation (default)
    (0, 1): 90,  # DOWN - 90° clockwise
    (-1, 0): 180,  # LEFT - 180°
    (0, -1): 270,  # UP - 270° clockwise (or 90° counter-clockwise)
}


class SnakeRenderSystem(BaseSystem):
    """System responsible for rendering snake entities with smooth interpolation.

    Responsibilities (following SRP):
    - Render snake head with interpolation
    - Render snake body segments with interpolation
    - Handle wraparound portal effects
    - Use colors from Palette component or ColorScheme fallback

    This system queries entities by components (Position, SnakeBody, Interpolation)
    rather than by entity type, following ECS data-driven principles.
    """

    def __init__(self, renderer: RenderEnqueue, settings=None, assets_system=None):
        """Initialize the SnakeRenderSystem.

        Args:
            renderer: RenderEnqueue view to queue draw commands
            settings: Optional game settings object for toggling features
            assets_system: Optional AssetsSystem for sprite access
        """
        self._renderer = renderer
        self._settings = settings
        self._assets = assets_system
        self._use_sprites = assets_system is not None

    def get_board_offset(self) -> tuple[int, int]:
        """Get the offset for the game board from screen edge.

        Returns:
            Tuple of (x_offset, y_offset) in pixels
        """
        # Get screen dimensions
        surface = pygame.display.get_surface()
        if not surface:
            return (0, 0)

        # Top offset for UI elements - use fixed 45px to ensure board fits completely
        top_offset = 45

        return (0, top_offset)

    def _get_color_scheme(self, world: World) -> ColorScheme:
        """Get ColorScheme component from world entities.

        Args:
            world: Game world

        Returns:
            ColorScheme component, or default if not found
        """
        color_entities = world.registry.query_by_component("color_scheme")

        if color_entities:
            entity = next(iter(color_entities.values()))
            return entity.color_scheme

        return ColorScheme()

    def draw_snake(
        self,
        world: World,
        position: Position,
        body: SnakeBody,
        interpolation: Interpolation,
        renderable=None,
    ) -> None:
        """Draw the snake with smooth interpolation.

        Args:
            world: Game world
            position: Head position component
            body: Snake body component
            interpolation: Interpolation component for smooth movement
            renderable: Optional renderable component for head color
        """
        if not body.alive:
            return

        cell_size = world.board.cell_size
        grid_width = world.board.width * cell_size
        grid_height = world.board.height * cell_size

        # Get colors from renderable or use constants as fallback
        # Check if rainbow mode is enabled (secondary_color with special marker)
        is_rainbow = False
        if renderable and hasattr(renderable, "color"):
            head_color = renderable.color.to_tuple()
            # Use secondary color for tail if available, otherwise derive from head or use constant
            if hasattr(renderable, "secondary_color") and renderable.secondary_color:
                # Check for rainbow mode marker (secondary color is pure green #00FF00 equivalent)
                # Rainbow mode uses a special marker in the secondary_color
                sec_color = renderable.secondary_color.to_tuple()
                # Rainbow marker: check if it's the special rainbow marker color
                if sec_color == (0, 0, 0):
                    # This is rainbow mode - marked by black secondary color
                    is_rainbow = True
                    tail_color = sec_color  # Will be overridden per-segment
                else:
                    tail_color = sec_color
            else:
                tail_color = Color.from_hex(constants.TAIL_COLOR).to_tuple()
        else:
            head_color = Color.from_hex(constants.HEAD_COLOR).to_tuple()
            tail_color = Color.from_hex(constants.TAIL_COLOR).to_tuple()

        # Draw tail segments
        self._draw_snake_tail(
            body,
            interpolation,
            position,
            cell_size,
            grid_width,
            grid_height,
            tail_color,
            world,
            is_rainbow,
            snake_velocity=(
                getattr(position, "prev_x", position.x) - position.x,
                getattr(position, "prev_y", position.y) - position.y,
            ),
        )

        # Draw head (get direction from velocity or position change)
        head_direction = self._get_head_direction(position)
        if is_rainbow:
            head_color = Color.from_hex(get_rainbow_color(0)).to_tuple()
        self._draw_snake_head(
            position,
            interpolation,
            cell_size,
            grid_width,
            grid_height,
            head_color,
            head_direction,
        )

    def _get_head_direction(self, position: Position) -> tuple[int, int]:
        """Determine head direction from position change."""
        dx = position.x - position.prev_x
        dy = position.y - position.prev_y
        # Normalize to unit direction (handle wraparound)
        if dx > 1:
            dx = -1
        elif dx < -1:
            dx = 1
        if dy > 1:
            dy = -1
        elif dy < -1:
            dy = 1
        # Default to DOWN if no movement
        if dx == 0 and dy == 0:
            return (0, 1)
        return (dx, dy)

    def _draw_snake_head(
        self,
        position: Position,
        interpolation: Interpolation,
        cell_size: int,
        grid_width: int,
        grid_height: int,
        color: tuple,
        direction: tuple[int, int] = (0, 1),
    ) -> None:
        """Draw the snake head with smooth interpolation and board offset.

        Args:
            position: Head position component
            interpolation: Interpolation component
            cell_size: Size of grid cells
            grid_width: Total grid width in pixels
            grid_height: Total grid height in pixels
            color: Head color as (r, g, b) tuple
            direction: Movement direction for sprite rotation
        """
        # Get board offset
        offset_x, offset_y = self.get_board_offset()

        # Calculate smooth interpolated position
        draw_x, draw_y = self._calculate_interpolated_position(
            position.x * cell_size,
            position.y * cell_size,
            position.prev_x * cell_size,
            position.prev_y * cell_size,
            interpolation.alpha,
            interpolation.wrapped_axis,
            cell_size,
            grid_width,
            grid_height,
        )

        # Apply board offset
        draw_x += offset_x
        draw_y += offset_y

        # Try sprite rendering first
        if self._use_sprites and self._assets:
            sprite = self._assets.get_tinted_snake_sprite("head", color, cell_size)
            if sprite:
                # Rotate sprite based on direction
                rotation = DIRECTION_TO_ROTATION.get(direction, 0)
                if rotation != 0:
                    sprite = pygame.transform.rotate(sprite, -rotation)
                self._renderer.blit(sprite, (int(draw_x), int(draw_y)))
            else:
                # Fallback to rectangle
                rect = pygame.Rect(int(draw_x), int(draw_y), cell_size, cell_size)
                self._renderer.draw_rect(color, rect, 0)
        else:
            # Rectangle rendering (fallback)
            rect = pygame.Rect(int(draw_x), int(draw_y), cell_size, cell_size)
            self._renderer.draw_rect(color, rect, 0)

            # Draw dark border for visual clarity at high speeds (if enabled)
            if self._settings and self._settings.get("segment_borders"):
                border_color = tuple(max(0, c - 60) for c in color)
                self._renderer.draw_rect(border_color, rect, 2)

        # Draw wraparound duplicate for smooth portal effect
        if interpolation.wrapped_axis != "none":
            self._draw_wraparound_duplicate(
                draw_x,
                draw_y,
                cell_size,
                grid_width,
                grid_height,
                interpolation.wrapped_axis,
                color,
            )

    def _draw_snake_tail(
        self,
        body: SnakeBody,
        interpolation: Interpolation,
        head_position: Position,
        cell_size: int,
        grid_width: int,
        grid_height: int,
        color: tuple,
        world: World = None,
        is_rainbow: bool = False,
        snake_velocity: tuple[int, int] = (0, 0),
    ) -> None:
        """Draw the snake tail with smooth interpolation for each segment and board offset.

        Args:
            body: Snake body component
            interpolation: Interpolation component
            head_position: Current head position
            cell_size: Size of grid cells
            grid_width: Total grid width in pixels
            grid_height: Total grid height in pixels
            color: Tail color as (r, g, b) tuple
            world: Optional world for checking game mode
            is_rainbow: Whether to use rainbow coloring for each segment
            snake_velocity: Snake movement velocity for direction calculation
        """
        if not body.segments:
            return

        # Get board offset
        offset_x, offset_y = self.get_board_offset()

        # Draw each tail segment
        for i, segment in enumerate(body.segments):
            draw_x, draw_y = self._calculate_interpolated_position(
                segment.x * cell_size,
                segment.y * cell_size,
                segment.prev_x * cell_size,
                segment.prev_y * cell_size,
                interpolation.alpha,
                interpolation.wrapped_axis,
                cell_size,
                grid_width,
                grid_height,
            )

            # Apply board offset
            draw_x += offset_x
            draw_y += offset_y

            # Determine segment color (rainbow cycles through colors)
            if is_rainbow:
                segment_color = Color.from_hex(get_rainbow_color(i + 1)).to_tuple()
            else:
                segment_color = color

            # Try sprite rendering
            if self._use_sprites and self._assets:
                # Determine segment type and rotation
                segment_type, rotation, flip_x, flip_y = self._get_segment_info(
                    body.segments, i, head_position
                )

                sprite = self._assets.get_tinted_snake_sprite(
                    segment_type, segment_color, cell_size
                )

                if sprite:
                    # Apply flip first, then rotation
                    if flip_x or flip_y:
                        sprite = pygame.transform.flip(sprite, flip_x, flip_y)
                    if rotation != 0:
                        sprite = pygame.transform.rotate(sprite, -rotation)
                    self._renderer.blit(sprite, (int(draw_x), int(draw_y)))
                else:
                    # Fallback to rectangle
                    segment_rect = pygame.Rect(
                        int(draw_x), int(draw_y), cell_size, cell_size
                    )
                    self._renderer.draw_rect(segment_color, segment_rect, 0)
            else:
                # Rectangle rendering (fallback)
                segment_rect = pygame.Rect(
                    int(draw_x), int(draw_y), cell_size, cell_size
                )
                self._renderer.draw_rect(segment_color, segment_rect, 0)

                # Draw dark border for visual clarity
                if self._settings and self._settings.get("segment_borders"):
                    border_color = tuple(max(0, c - 60) for c in segment_color)
                    self._renderer.draw_rect(border_color, segment_rect, 2)

            # Draw wraparound duplicate
            if interpolation.wrapped_axis != "none":
                self._draw_wraparound_duplicate(
                    draw_x,
                    draw_y,
                    cell_size,
                    grid_width,
                    grid_height,
                    interpolation.wrapped_axis,
                    segment_color,
                )

    def _get_segment_info(
        self,
        segments: list,
        index: int,
        head_position: Position,
    ) -> tuple[str, int]:
        """Determine segment type and rotation angle.

        Args:
            segments: List of body segments
            index: Current segment index
            head_position: Position of the snake head

        Returns:
            Tuple of (segment_type, rotation_angle, flip_x, flip_y)
            segment_type: "body", "turn", or "tail"
            rotation_angle: Degrees to rotate (0, 90, 180, 270)
            flip_x, flip_y: Whether to flip horizontally/vertically
        """
        curr = segments[index]

        # TAIL (last segment)
        if index == len(segments) - 1:
            if index == 0:
                # Only segment - use direction from head
                prev = head_position
            else:
                prev = segments[index - 1]
            direction = self._normalize_direction(curr.x - prev.x, curr.y - prev.y)
            # Tail points AWAY from body, so add 180° to flip it
            rotation = (DIRECTION_TO_ROTATION.get(direction, 0) + 180) % 360
            return ("tail", rotation, False, False)

        # Get adjacent positions for direction calculation
        if index == 0:
            prev = head_position
        else:
            prev = segments[index - 1]
        next_seg = segments[index + 1]

        # Calculate incoming and outgoing directions
        dir_in = self._normalize_direction(curr.x - prev.x, curr.y - prev.y)
        dir_out = self._normalize_direction(next_seg.x - curr.x, next_seg.y - curr.y)

        # STRAIGHT BODY (same direction in and out)
        if dir_in == dir_out:
            # Body sprite is horizontal by default (facing RIGHT)
            if dir_in[0] != 0:  # Horizontal movement (LEFT/RIGHT)
                rotation = 0  # No rotation needed
            else:  # Vertical movement (UP/DOWN)
                rotation = 90  # Rotate 90° for vertical
            return ("body", rotation, False, False)

        # TURN segment (direction changes)
        rotation, flip_x, flip_y = self._calculate_turn_rotation(dir_in, dir_out)
        return ("turn", rotation, flip_x, flip_y)

    def _normalize_direction(self, dx: int, dy: int) -> tuple[int, int]:
        """Normalize direction to unit vector, handling wraparound."""
        if dx > 1:
            dx = -1
        elif dx < -1:
            dx = 1
        if dy > 1:
            dy = -1
        elif dy < -1:
            dy = 1
        # Clamp to -1, 0, 1
        if dx != 0:
            dx = 1 if dx > 0 else -1
        if dy != 0:
            dy = 1 if dy > 0 else -1
        return (dx, dy)

    def _calculate_turn_rotation(
        self, dir_in: tuple[int, int], dir_out: tuple[int, int]
    ) -> tuple[int, bool, bool]:
        """Calculate rotation for a turn segment.

        Default sprite (0°) connects LEFT-UP corner shape.
        Rotation-only approach:
        - 0°: LEFT→UP, DOWN→RIGHT
        - 90° CW: LEFT→DOWN, UP→RIGHT
        - 180°: RIGHT→DOWN, UP→LEFT
        - 270° (90° CCW): RIGHT→UP, DOWN→LEFT

        Returns:
            Tuple of (rotation_degrees, flip_x, flip_y) - flip always False
        """
        turn_map = {
            # 0° - default corner shape (LEFT-UP / DOWN-RIGHT)
            ((-1, 0), (0, -1)): (0, False, False),  # LEFT → UP
            ((0, 1), (1, 0)): (0, False, False),  # DOWN → RIGHT
            # 90° CW - rotated corner (LEFT-DOWN / UP-RIGHT)
            ((-1, 0), (0, 1)): (90, False, False),  # LEFT → DOWN
            ((0, -1), (1, 0)): (90, False, False),  # UP → RIGHT
            # 180° - opposite corner (RIGHT-DOWN / UP-LEFT)
            ((1, 0), (0, 1)): (180, False, False),  # RIGHT → DOWN
            ((0, -1), (-1, 0)): (180, False, False),  # UP → LEFT
            # 270° (90° CCW) - other corner (RIGHT-UP / DOWN-LEFT)
            ((1, 0), (0, -1)): (270, False, False),  # RIGHT → UP
            ((0, 1), (-1, 0)): (270, False, False),  # DOWN → LEFT
        }
        return turn_map.get((dir_in, dir_out), (0, False, False))

    def _calculate_interpolated_position(
        self,
        current_x: int,
        current_y: int,
        prev_x: int,
        prev_y: int,
        alpha: float,
        wrapped_axis: str,
        cell_size: int,
        grid_width: int,
        grid_height: int,
    ) -> tuple[float, float]:
        """Calculate interpolated position with edge wrapping support.

        Args:
            current_x: Current x position
            current_y: Current y position
            prev_x: Previous x position
            prev_y: Previous y position
            alpha: Interpolation factor [0.0, 1.0]
            wrapped_axis: Which axis wrapped ("none", "x", "y", "both")
            cell_size: Size of grid cells
            grid_width: Total grid width in pixels
            grid_height: Total grid height in pixels

        Returns:
            Tuple of (interpolated_x, interpolated_y)
        """
        draw_x = prev_x + (current_x - prev_x) * alpha
        draw_y = prev_y + (current_y - prev_y) * alpha

        # Handle wrapping on x-axis
        if wrapped_axis in ("x", "both"):
            if abs(current_x - prev_x) > grid_width / 2:
                if current_x < prev_x:
                    draw_x = prev_x + alpha * cell_size
                else:
                    draw_x = prev_x - alpha * cell_size

        # Handle wrapping on y-axis
        if wrapped_axis in ("y", "both"):
            if abs(current_y - prev_y) > grid_height / 2:
                if current_y < prev_y:
                    draw_y = prev_y + alpha * cell_size
                else:
                    draw_y = prev_y - alpha * cell_size

        # Wrap coordinates to stay within grid bounds
        draw_x = draw_x % grid_width
        draw_y = draw_y % grid_height

        return (draw_x, draw_y)

    def _draw_wraparound_duplicate(
        self,
        draw_x: float,
        draw_y: float,
        cell_size: int,
        grid_width: int,
        grid_height: int,
        wrapped_axis: str,
        color: tuple,
    ) -> None:
        """Draw duplicate of segment on opposite edge for smooth wraparound.

        Args:
            draw_x: Current X position
            draw_y: Current Y position
            cell_size: Size of grid cells
            grid_width: Total grid width in pixels
            grid_height: Total grid height in pixels
            wrapped_axis: Which axis wrapped
            color: Segment color
        """
        dup_x = draw_x
        dup_y = draw_y

        if wrapped_axis in ("x", "both"):
            if draw_x >= grid_width - cell_size:
                dup_x = draw_x - grid_width
            elif draw_x < cell_size:
                dup_x = draw_x + grid_width

        if wrapped_axis in ("y", "both"):
            if draw_y >= grid_height - cell_size:
                dup_y = draw_y - grid_height
            elif draw_y < cell_size:
                dup_y = draw_y + grid_height

        # Only draw duplicate if position actually changed
        if dup_x != draw_x or dup_y != draw_y:
            dup_rect = pygame.Rect(int(dup_x), int(dup_y), cell_size, cell_size)
            self._renderer.draw_rect(color, dup_rect, 0)

    def update(self, world: World) -> None:
        """Update method required by BaseSystem.

        Renders all snake entities with smooth interpolation.
        Queries entities by components rather than type.

        Args:
            world: Game world to render
        """
        # Query snakes by required components (ECS data-driven approach)
        snakes = world.registry.query_by_type_and_components(
            EntityType.SNAKE, "position", "body", "interpolation"
        )

        for _, snake in snakes.items():
            # Get components
            position = snake.position
            body = snake.body
            interpolation = snake.interpolation
            renderable = getattr(snake, "renderable", None)

            # Render snake
            self.draw_snake(world, position, body, interpolation, renderable)
