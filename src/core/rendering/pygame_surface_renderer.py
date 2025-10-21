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

    def draw_start_menu(self, menu_items: list[str], selected_index: int) -> None:
        self._impl.draw_start_menu(menu_items, selected_index)

    def draw_settings_menu(
        self, settings_fields: list[dict], selected_index: int, settings_values: dict
    ) -> None:
        self._impl.draw_settings_menu(settings_fields, selected_index, settings_values)

    def draw_reset_warning_dialog(self, selected_option: int) -> None:
        self._impl.draw_reset_warning_dialog(selected_option)

    def draw_game_over_screen(self, final_score: int, selected_option: int) -> None:
        self._impl.draw_game_over_screen(final_score, selected_option)


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

    def draw_start_menu(self, menu_items: list[str], selected_index: int) -> None:
        """Queue start menu rendering operation.

        Args:
            menu_items: List of menu item text strings
            selected_index: Index of currently selected item
        """

        # Create a command that will render the start menu
        def _render_start_menu(surface, items, selected):
            width, height = surface.get_size()

            # Colors (hardcoded for now, should come from settings)
            title_color = (255, 255, 255)  # White
            selected_color = (255, 255, 255)  # White
            unselected_color = (128, 128, 128)  # Gray

            # Create fonts
            title_font = pygame.font.Font(
                "assets/font/GetVoIP-Grotesque.ttf", int(width / 12)
            )
            menu_font = pygame.font.Font(
                "assets/font/GetVoIP-Grotesque.ttf", int(width / 20)
            )

            # Render title
            title_text = title_font.render("Naja", True, title_color)
            title_rect = title_text.get_rect(center=(width // 2, height // 4))
            surface.blit(title_text, title_rect)

            # Render menu items
            for i, item in enumerate(items):
                color = selected_color if i == selected else unselected_color
                text = menu_font.render(item, True, color)
                rect = text.get_rect(
                    center=(width // 2, height // 2 + i * (height * 0.12))
                )
                surface.blit(text, rect)

        self._command_queue.append(
            DrawCommand(
                operation=_render_start_menu,
                args=(self._surface, menu_items, selected_index),
                kwargs={},
            )
        )

    def draw_settings_menu(
        self, settings_fields: list[dict], selected_index: int, settings_values: dict
    ) -> None:
        """Queue settings menu rendering operation.

        Args:
            settings_fields: List of setting field definitions
            selected_index: Index of currently selected field
            settings_values: Current values of all settings
        """

        def _render_settings_menu(surface, fields, selected, values):
            width, height = surface.get_size()

            # Colors
            title_color = (255, 255, 255)  # White
            selected_color = (255, 255, 255)  # White
            unselected_color = (128, 128, 128)  # Gray
            hint_color = (96, 96, 96)  # Dark gray

            # Create fonts
            title_font = pygame.font.Font(
                "assets/font/GetVoIP-Grotesque.ttf", int(width / 12)
            )
            field_font = pygame.font.Font(
                "assets/font/GetVoIP-Grotesque.ttf", int(width / 30)
            )
            hint_font = pygame.font.Font(
                "assets/font/GetVoIP-Grotesque.ttf", int(width / 50)
            )

            # Render title
            title_text = title_font.render("Settings", True, title_color)
            title_rect = title_text.get_rect(center=(width // 2, height // 10))
            surface.blit(title_text, title_rect)

            # Render settings fields
            row_height = int(height * 0.06)
            start_y = int(height * 0.22)

            for i, field in enumerate(fields):
                if i >= len(fields):
                    break

                value = values.get(field["key"], "")
                color = selected_color if i == selected else unselected_color

                # Format the value display
                if field["type"] == "bool":
                    display_value = "ON" if value else "OFF"
                elif field["type"] == "select":
                    display_value = str(value)
                else:
                    display_value = str(value)

                text = field_font.render(
                    f"{field['label']}: {display_value}", True, color
                )
                rect = text.get_rect()
                rect.left = int(width * 0.10)
                rect.top = start_y + i * row_height
                surface.blit(text, rect)

            # Render hint
            hint_text = "[A/D] change   [W/S] select   [Enter/Esc] back"
            hint = hint_font.render(hint_text, True, hint_color)
            hint_rect = hint.get_rect(center=(width // 2, int(height * 0.95)))
            surface.blit(hint, hint_rect)

        self._command_queue.append(
            DrawCommand(
                operation=_render_settings_menu,
                args=(self._surface, settings_fields, selected_index, settings_values),
                kwargs={},
            )
        )

    def draw_reset_warning_dialog(self, selected_option: int) -> None:
        """Queue reset warning dialog rendering operation.

        Args:
            selected_option: Index of currently selected option (0=Reset, 1=Cancel)
        """

        def _render_reset_warning(surface, selected):
            width, height = surface.get_size()

            # Colors
            title_color = (255, 255, 255)  # White
            message_color = (200, 200, 200)  # Light gray
            selected_color = (255, 255, 255)  # White
            unselected_color = (128, 128, 128)  # Gray

            # Create fonts
            title_font = pygame.font.Font(
                "assets/font/GetVoIP-Grotesque.ttf", int(width / 8)
            )
            message_font = pygame.font.Font(
                "assets/font/GetVoIP-Grotesque.ttf", int(width / 20)
            )
            option_font = pygame.font.Font(
                "assets/font/GetVoIP-Grotesque.ttf", int(width / 25)
            )

            # Render title
            title_text = title_font.render("Reset Required", True, title_color)
            title_rect = title_text.get_rect(center=(width // 2, height // 3))
            surface.blit(title_text, title_rect)

            # Render message
            message_text = message_font.render(
                "This change requires resetting the game. Continue?",
                True,
                message_color,
            )
            message_rect = message_text.get_rect(center=(width // 2, height // 2))
            surface.blit(message_text, message_rect)

            # Render options
            options = ["Yes (Reset)", "No (Cancel)"]
            option_y = int(height * 0.6)

            for i, option in enumerate(options):
                color = selected_color if i == selected else unselected_color
                text = option_font.render(option, True, color)
                rect = text.get_rect(center=(width // 2, option_y + i * 40))
                surface.blit(text, rect)

        self._command_queue.append(
            DrawCommand(
                operation=_render_reset_warning,
                args=(self._surface, selected_option),
                kwargs={},
            )
        )

    def draw_game_over_screen(self, final_score: int, selected_option: int) -> None:
        """Queue game over screen rendering operation.

        Args:
            final_score: Final score to display
            selected_option: Index of currently selected option (0=Restart, 1=Quit)
        """

        def _render_game_over(surface, score, selected):
            width, height = surface.get_size()

            # Colors
            title_color = (255, 100, 100)  # Red
            score_color = (255, 255, 255)  # White
            selected_color = (255, 255, 255)  # White
            unselected_color = (128, 128, 128)  # Gray

            # Create fonts
            title_font = pygame.font.Font(
                "assets/font/GetVoIP-Grotesque.ttf", int(width / 6)
            )
            score_font = pygame.font.Font(
                "assets/font/GetVoIP-Grotesque.ttf", int(width / 15)
            )
            option_font = pygame.font.Font(
                "assets/font/GetVoIP-Grotesque.ttf", int(width / 20)
            )

            # Render title
            title_text = title_font.render("Game Over", True, title_color)
            title_rect = title_text.get_rect(center=(width // 2, height // 3))
            surface.blit(title_text, title_rect)

            # Render score
            score_text = score_font.render(f"Final Score: {score}", True, score_color)
            score_rect = score_text.get_rect(center=(width // 2, height // 2))
            surface.blit(score_text, score_rect)

            # Render options
            options = ["Restart", "Quit"]
            option_y = int(height * 0.65)

            for i, option in enumerate(options):
                color = selected_color if i == selected else unselected_color
                text = option_font.render(option, True, color)
                rect = text.get_rect(center=(width // 2, option_y + i * 50))
                surface.blit(text, rect)

        self._command_queue.append(
            DrawCommand(
                operation=_render_game_over,
                args=(self._surface, final_score, selected_option),
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
