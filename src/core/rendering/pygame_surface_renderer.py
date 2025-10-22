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

"""PygameSurfaceRenderer - command queue wrapper for pygame surface operations."""

from typing import Protocol, Optional
from dataclasses import dataclass
import pygame


@dataclass
class DrawCommand:
    """Represents a single draw command to be executed.

    Attributes:
        operation: The pygame drawing function to call
        args: Positional arguments for the operation
        kwargs: Keyword arguments for the operation
    """

    operation: callable
    args: tuple
    kwargs: dict


class RenderEnqueue(Protocol):
    """Protocol defining read-only surface properties and enqueue-only operations.

    Systems receive this interface to queue draw commands without access to
    frame control methods (begin_frame, update).
    """

    @property
    def width(self) -> int: ...
    @property
    def height(self) -> int: ...
    @property
    def size(self) -> tuple[int, int]: ...
    def get_size(self) -> tuple[int, int]: ...
    def fill(self, color: tuple[int, int, int] | tuple[int, int, int, int]) -> None: ...
    def blit(
        self,
        source: pygame.Surface,
        dest: tuple[int, int] | pygame.Rect,
        area: Optional[pygame.Rect] = None,
        special_flags: int = 0,
    ) -> None: ...
    def draw_line(
        self,
        color: tuple[int, int, int],
        start_pos: tuple[int, int],
        end_pos: tuple[int, int],
        width: int = 1,
    ) -> None: ...
    def draw_rect(
        self, color: tuple[int, int, int], rect: pygame.Rect, width: int = 0
    ) -> None: ...
    def draw_settings_menu(
        self, settings_fields: list[dict], selected_index: int, settings_values: dict
    ) -> None: ...
    def draw_reset_warning_dialog(self, selected_option: int) -> None: ...
    def draw_game_over_screen(self, final_score: int, selected_option: int) -> None: ...


class _RendererView(RenderEnqueue):
    """Enqueue-only view of the renderer.

    This view exposes only read-only properties and draw command queueing.
    Frame control methods (begin_frame, update) are NOT exposed, preventing
    systems from interfering with the rendering pipeline.
    """

    def __init__(self, impl: "PygameSurfaceRenderer"):
        """Initialize the view with a reference to the renderer implementation.

        Args:
            impl: The actual PygameSurfaceRenderer instance
        """
        self._impl = impl

    # Read-only properties
    @property
    def width(self) -> int:
        return self._impl.width

    @property
    def height(self) -> int:
        return self._impl.height

    @property
    def size(self) -> tuple[int, int]:
        return self._impl.size

    def get_size(self) -> tuple[int, int]:
        return self._impl.get_size()

    # Enqueue methods delegate to implementation
    def fill(self, color: tuple[int, int, int] | tuple[int, int, int, int]) -> None:
        self._impl.fill(color)

    def blit(
        self,
        source: pygame.Surface,
        dest: tuple[int, int] | pygame.Rect,
        area: Optional[pygame.Rect] = None,
        special_flags: int = 0,
    ) -> None:
        self._impl.blit(source, dest, area, special_flags)

    def draw_line(
        self,
        color: tuple[int, int, int],
        start_pos: tuple[int, int],
        end_pos: tuple[int, int],
        width: int = 1,
    ) -> None:
        self._impl.draw_line(color, start_pos, end_pos, width)

    def draw_rect(
        self, color: tuple[int, int, int], rect: pygame.Rect, width: int = 0
    ) -> None:
        self._impl.draw_rect(color, rect, width)


class PygameSurfaceRenderer:
    """Command queue wrapper for pygame surface rendering operations.

    This class provides a pygame.Surface-like interface but queues all draw
    operations internally. Commands are executed sequentially when update()
    is called, providing centralized control over rendering order.

    Benefits:
    - Decouples systems from direct pygame surface access
    - Provides clear rendering order (commands executed in queue order)
    - Exposes read-only display properties (width, height, size)
    - Future-proof for potential rendering optimizations (batching, culling)
    - Two-tier access model:
      * Full access (with update): For main/core rendering loop
      * Enqueue-only view: For systems (prevents interference with pipeline)

    Usage:
        # Main loop has full access
        renderer = PygameSurfaceRenderer(screen)

        # Systems get enqueue-only view
        enqueue_view = renderer.view()
        system = BoardRenderSystem(enqueue_view)

        # Main loop controls frame lifecycle
        renderer.begin_frame()
        system.update(world)
        renderer.update()

    Attributes:
        _surface: The underlying pygame surface
        _command_queue: List of draw commands to execute
    """

    def __init__(self, surface: pygame.Surface):
        """Initialize the renderer with a pygame surface.

        Args:
            surface: The pygame surface to render to
        """
        self._surface = surface
        self._command_queue: list[DrawCommand] = []

    # Read-only properties for display information

    @property
    def width(self) -> int:
        """Get the width of the surface in pixels.

        Returns:
            int: Width in pixels
        """
        return self._surface.get_width()

    @property
    def height(self) -> int:
        """Get the height of the surface in pixels.

        Returns:
            int: Height in pixels
        """
        return self._surface.get_height()

    @property
    def size(self) -> tuple[int, int]:
        """Get the size of the surface as (width, height).

        Returns:
            tuple[int, int]: (width, height) in pixels
        """
        return self._surface.get_size()

    # Surface-like methods that queue commands

    def get_size(self) -> tuple[int, int]:
        """Get the size of the surface as (width, height).

        This method is provided for pygame.Surface compatibility.

        Returns:
            tuple[int, int]: (width, height) in pixels
        """
        return self._surface.get_size()

    def fill(self, color: tuple[int, int, int] | tuple[int, int, int, int]) -> None:
        """Queue a fill operation to clear the surface with a color.

        Args:
            color: RGB or RGBA color tuple
        """
        self._command_queue.append(
            DrawCommand(operation=self._surface.fill, args=(color,), kwargs={})
        )

    def blit(
        self,
        source: pygame.Surface,
        dest: tuple[int, int] | pygame.Rect,
        area: pygame.Rect | None = None,
        special_flags: int = 0,
    ) -> None:
        """Queue a blit operation to draw a surface onto this surface.

        Args:
            source: Source surface to draw
            dest: Destination position (x, y) or Rect
            area: Optional area of source surface to draw
            special_flags: Optional special blending flags
        """
        kwargs = {}
        if area is not None:
            kwargs["area"] = area
        if special_flags != 0:
            kwargs["special_flags"] = special_flags

        self._command_queue.append(
            DrawCommand(
                operation=self._surface.blit, args=(source, dest), kwargs=kwargs
            )
        )

    def draw_line(
        self,
        color: tuple[int, int, int],
        start_pos: tuple[int, int],
        end_pos: tuple[int, int],
        width: int = 1,
    ) -> None:
        """Queue a line drawing operation.

        Args:
            color: RGB color tuple
            start_pos: Starting position (x, y)
            end_pos: Ending position (x, y)
            width: Line width in pixels
        """
        self._command_queue.append(
            DrawCommand(
                operation=pygame.draw.line,
                args=(self._surface, color, start_pos, end_pos, width),
                kwargs={},
            )
        )

    def draw_rect(
        self, color: tuple[int, int, int], rect: pygame.Rect, width: int = 0
    ) -> None:
        """Queue a rectangle drawing operation.

        Args:
            color: RGB color tuple
            rect: Rectangle to draw
            width: Line width (0 for filled rectangle)
        """
        self._command_queue.append(
            DrawCommand(
                operation=pygame.draw.rect,
                args=(self._surface, color, rect, width),
                kwargs={},
            )
        )

    # Frame control methods (only for main/core, not exposed in view)

    def begin_frame(
        self, clear_color: tuple[int, int, int, int] = (0, 0, 0, 0)
    ) -> None:
        """Begin a new frame by clearing the surface and command queue.

        This should be called at the start of each frame by the main rendering loop.

        Args:
            clear_color: RGBA color to clear the surface with (default: transparent black)
        """
        self._surface.fill(clear_color)
        self._command_queue.clear()

    def update(self) -> None:
        """Execute all queued draw commands and update the display.

        This method:
        1. Executes all queued commands in order
        2. Clears the command queue
        3. Updates the pygame display

        This should be called once per frame after all systems have queued
        their draw operations. Only the main rendering loop should call this.
        """
        # Execute all queued commands in order
        for command in self._command_queue:
            command.operation(*command.args, **command.kwargs)

        # Clear the queue for next frame
        self._command_queue.clear()

        # Update the display
        pygame.display.update()

    # View factory method

    def view(self) -> RenderEnqueue:
        """Create an enqueue-only view of this renderer.

        The view exposes only read-only properties and draw command queueing.
        Frame control methods (begin_frame, update) are NOT accessible through
        the view, ensuring systems cannot interfere with the rendering pipeline.

        Returns:
            RenderEnqueue: An enqueue-only view of this renderer

        Usage:
            renderer = PygameSurfaceRenderer(screen)
            view = renderer.view()
            system = BoardRenderSystem(view)  # System can't call update()
        """
        return _RendererView(self)
