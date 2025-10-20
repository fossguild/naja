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

"""Unit tests for PygameSurfaceRenderer."""

import pytest
import pygame
from unittest.mock import Mock, MagicMock, patch
from src.core.rendering.pygame_surface_renderer import (
    PygameSurfaceRenderer,
    RenderEnqueue,
    _RendererView,
    DrawCommand,
)


@pytest.fixture(scope="module")
def pygame_init():
    """Initialize pygame once for all tests."""
    pygame.init()
    pygame.display.init()
    yield
    pygame.quit()


@pytest.fixture
def mock_surface():
    """Provide a mock pygame surface."""
    surface = MagicMock(spec=pygame.Surface)
    surface.get_width.return_value = 800
    surface.get_height.return_value = 600
    surface.get_size.return_value = (800, 600)
    return surface


@pytest.fixture
def renderer(mock_surface):
    """Provide a PygameSurfaceRenderer instance."""
    return PygameSurfaceRenderer(mock_surface)


@pytest.fixture
def real_surface(pygame_init):
    """Provide a real pygame surface for integration tests."""
    return pygame.Surface((800, 600))


class TestDrawCommand:
    """Tests for DrawCommand dataclass."""

    def test_draw_command_creation(self):
        """Test that DrawCommand can be created with operation, args, kwargs."""
        operation = Mock()
        args = (1, 2, 3)
        kwargs = {"key": "value"}

        cmd = DrawCommand(operation=operation, args=args, kwargs=kwargs)

        assert cmd.operation is operation
        assert cmd.args == args
        assert cmd.kwargs == kwargs


class TestPygameSurfaceRendererInitialization:
    """Tests for PygameSurfaceRenderer initialization."""

    def test_initialization(self, mock_surface):
        """Test that renderer initializes correctly."""
        renderer = PygameSurfaceRenderer(mock_surface)

        assert renderer._surface is mock_surface
        assert isinstance(renderer._command_queue, list)
        assert len(renderer._command_queue) == 0

    def test_initialization_with_real_surface(self, real_surface):
        """Test initialization with a real pygame surface."""
        renderer = PygameSurfaceRenderer(real_surface)

        assert renderer._surface is real_surface
        assert len(renderer._command_queue) == 0


class TestRendererProperties:
    """Tests for read-only properties."""

    def test_width_property(self, renderer):
        """Test that width property returns surface width."""
        assert renderer.width == 800

    def test_height_property(self, renderer):
        """Test that height property returns surface height."""
        assert renderer.height == 600

    def test_size_property(self, renderer):
        """Test that size property returns (width, height)."""
        assert renderer.size == (800, 600)

    def test_get_size_method(self, renderer):
        """Test that get_size method returns (width, height)."""
        assert renderer.get_size() == (800, 600)


class TestCommandQueueing:
    """Tests for command queueing operations."""

    def test_fill_queues_command(self, renderer):
        """Test that fill queues a fill command."""
        color = (255, 0, 0)

        renderer.fill(color)

        assert len(renderer._command_queue) == 1
        cmd = renderer._command_queue[0]
        assert cmd.operation == renderer._surface.fill
        assert cmd.args == (color,)
        assert cmd.kwargs == {}

    def test_fill_with_rgba(self, renderer):
        """Test that fill works with RGBA color."""
        color = (255, 0, 0, 128)

        renderer.fill(color)

        assert len(renderer._command_queue) == 1
        assert renderer._command_queue[0].args == (color,)

    def test_blit_queues_command(self, renderer):
        """Test that blit queues a blit command."""
        source = Mock(spec=pygame.Surface)
        dest = (10, 20)

        renderer.blit(source, dest)

        assert len(renderer._command_queue) == 1
        cmd = renderer._command_queue[0]
        assert cmd.operation == renderer._surface.blit
        assert cmd.args == (source, dest)
        assert cmd.kwargs == {}

    def test_blit_with_area(self, renderer):
        """Test that blit with area parameter includes it in kwargs."""
        source = Mock(spec=pygame.Surface)
        dest = (10, 20)
        area = pygame.Rect(0, 0, 50, 50)

        renderer.blit(source, dest, area=area)

        cmd = renderer._command_queue[0]
        assert cmd.kwargs == {"area": area}

    def test_blit_with_special_flags(self, renderer):
        """Test that blit with special flags includes them in kwargs."""
        source = Mock(spec=pygame.Surface)
        dest = (10, 20)
        flags = pygame.BLEND_ADD

        renderer.blit(source, dest, special_flags=flags)

        cmd = renderer._command_queue[0]
        assert cmd.kwargs == {"special_flags": flags}

    def test_draw_line_queues_command(self, renderer):
        """Test that draw_line queues a line drawing command."""
        color = (255, 255, 0)
        start = (0, 0)
        end = (100, 100)

        renderer.draw_line(color, start, end)

        assert len(renderer._command_queue) == 1
        cmd = renderer._command_queue[0]
        assert cmd.operation == pygame.draw.line
        assert cmd.args == (renderer._surface, color, start, end, 1)

    def test_draw_line_with_width(self, renderer):
        """Test that draw_line with width parameter."""
        color = (255, 255, 0)
        start = (0, 0)
        end = (100, 100)
        width = 5

        renderer.draw_line(color, start, end, width=width)

        cmd = renderer._command_queue[0]
        assert cmd.args == (renderer._surface, color, start, end, width)

    def test_draw_rect_queues_command(self, renderer):
        """Test that draw_rect queues a rectangle drawing command."""
        color = (0, 255, 0)
        rect = pygame.Rect(10, 10, 50, 50)

        renderer.draw_rect(color, rect)

        assert len(renderer._command_queue) == 1
        cmd = renderer._command_queue[0]
        assert cmd.operation == pygame.draw.rect
        assert cmd.args == (renderer._surface, color, rect, 0)

    def test_draw_rect_with_width(self, renderer):
        """Test that draw_rect with width parameter (outline)."""
        color = (0, 255, 0)
        rect = pygame.Rect(10, 10, 50, 50)
        width = 3

        renderer.draw_rect(color, rect, width=width)

        cmd = renderer._command_queue[0]
        assert cmd.args == (renderer._surface, color, rect, width)

    def test_multiple_commands_queued_in_order(self, renderer):
        """Test that multiple commands are queued in order."""
        renderer.fill((0, 0, 0))
        renderer.draw_line((255, 0, 0), (0, 0), (100, 100))
        renderer.draw_rect((0, 255, 0), pygame.Rect(10, 10, 50, 50))

        assert len(renderer._command_queue) == 3
        assert renderer._command_queue[0].operation == renderer._surface.fill
        assert renderer._command_queue[1].operation == pygame.draw.line
        assert renderer._command_queue[2].operation == pygame.draw.rect


class TestFrameControl:
    """Tests for frame control methods."""

    def test_begin_frame_clears_surface(self, renderer):
        """Test that begin_frame clears the surface."""
        clear_color = (50, 50, 50, 255)

        renderer.begin_frame(clear_color)

        renderer._surface.fill.assert_called_once_with(clear_color)

    def test_begin_frame_clears_command_queue(self, renderer):
        """Test that begin_frame clears the command queue."""
        # Add some commands
        renderer.fill((255, 0, 0))
        renderer.draw_line((0, 255, 0), (0, 0), (100, 100))
        assert len(renderer._command_queue) == 2

        renderer.begin_frame()

        assert len(renderer._command_queue) == 0

    def test_begin_frame_default_color(self, renderer):
        """Test that begin_frame uses default transparent black."""
        renderer.begin_frame()

        renderer._surface.fill.assert_called_once_with((0, 0, 0, 0))

    @patch("pygame.display.update")
    def test_update_executes_commands(self, mock_display_update, real_surface):
        """Test that update executes all queued commands."""
        renderer = PygameSurfaceRenderer(real_surface)

        # Queue some commands (using real surface for pygame.draw operations)
        renderer.fill((0, 0, 0))
        renderer.draw_line((255, 0, 0), (0, 0), (100, 100))

        assert len(renderer._command_queue) == 2

        renderer.update()

        # Commands should have been executed (queue cleared)
        assert len(renderer._command_queue) == 0

        # Should have called display.update
        mock_display_update.assert_called_once()

    @patch("pygame.display.update")
    def test_update_clears_queue(self, mock_display_update, real_surface):
        """Test that update clears the command queue after execution."""
        renderer = PygameSurfaceRenderer(real_surface)

        renderer.fill((0, 0, 0))
        renderer.draw_line((255, 0, 0), (0, 0), (100, 100))

        assert len(renderer._command_queue) == 2

        renderer.update()

        assert len(renderer._command_queue) == 0

    @patch("pygame.display.update")
    def test_update_executes_commands_in_order(self, mock_display_update, real_surface):
        """Test that commands are executed in the order they were queued."""
        renderer = PygameSurfaceRenderer(real_surface)

        # Queue commands in specific order
        renderer.fill((0, 0, 0))
        renderer.draw_rect((255, 0, 0), pygame.Rect(10, 10, 50, 50))
        renderer.draw_line((0, 255, 0), (0, 0), (100, 100))

        # Verify all commands are queued
        assert len(renderer._command_queue) == 3

        # First command should be fill
        assert renderer._command_queue[0].operation == real_surface.fill

        # Second command should be draw.rect
        assert renderer._command_queue[1].operation == pygame.draw.rect

        # Third command should be draw.line
        assert renderer._command_queue[2].operation == pygame.draw.line

        # Update executes them (we can verify by checking queue is cleared)
        renderer.update()

        assert len(renderer._command_queue) == 0
        mock_display_update.assert_called_once()


class TestRendererView:
    """Tests for the enqueue-only view."""

    def test_view_creation(self, renderer):
        """Test that view() creates a _RendererView instance."""
        view = renderer.view()

        assert isinstance(view, _RendererView)
        assert view._impl is renderer

    def test_view_satisfies_protocol(self, renderer):
        """Test that view satisfies RenderEnqueue protocol."""
        view = renderer.view()

        # Check that view has all required protocol methods/properties
        assert hasattr(view, "width")
        assert hasattr(view, "height")
        assert hasattr(view, "size")
        assert hasattr(view, "get_size")
        assert hasattr(view, "fill")
        assert hasattr(view, "blit")
        assert hasattr(view, "draw_line")
        assert hasattr(view, "draw_rect")

    def test_view_properties_delegate_to_renderer(self, renderer):
        """Test that view properties return renderer values."""
        view = renderer.view()

        assert view.width == renderer.width
        assert view.height == renderer.height
        assert view.size == renderer.size
        assert view.get_size() == renderer.get_size()

    def test_view_fill_delegates_to_renderer(self, renderer):
        """Test that view.fill queues command in renderer."""
        view = renderer.view()
        color = (100, 100, 100)

        view.fill(color)

        assert len(renderer._command_queue) == 1
        assert renderer._command_queue[0].args == (color,)

    def test_view_blit_delegates_to_renderer(self, renderer):
        """Test that view.blit queues command in renderer."""
        view = renderer.view()
        source = Mock(spec=pygame.Surface)
        dest = (50, 50)

        view.blit(source, dest)

        assert len(renderer._command_queue) == 1
        assert renderer._command_queue[0].args == (source, dest)

    def test_view_draw_line_delegates_to_renderer(self, renderer):
        """Test that view.draw_line queues command in renderer."""
        view = renderer.view()
        color = (255, 0, 0)
        start = (10, 10)
        end = (90, 90)

        view.draw_line(color, start, end)

        assert len(renderer._command_queue) == 1

    def test_view_draw_rect_delegates_to_renderer(self, renderer):
        """Test that view.draw_rect queues command in renderer."""
        view = renderer.view()
        color = (0, 255, 0)
        rect = pygame.Rect(20, 20, 60, 60)

        view.draw_rect(color, rect)

        assert len(renderer._command_queue) == 1

    def test_view_does_not_expose_update(self, renderer):
        """Test that view does NOT expose update method."""
        view = renderer.view()

        assert not hasattr(view, "update")

    def test_view_does_not_expose_begin_frame(self, renderer):
        """Test that view does NOT expose begin_frame method."""
        view = renderer.view()

        assert not hasattr(view, "begin_frame")

    def test_multiple_views_share_same_queue(self, renderer):
        """Test that multiple views operate on the same command queue."""
        view1 = renderer.view()
        view2 = renderer.view()

        view1.fill((255, 0, 0))
        view2.fill((0, 255, 0))

        # Both should queue to the same renderer
        assert len(renderer._command_queue) == 2


class TestIntegration:
    """Integration tests with real pygame surfaces."""

    @patch("pygame.display.update")
    def test_full_render_cycle(self, mock_display_update, real_surface):
        """Test a complete render cycle: begin -> queue -> update."""
        renderer = PygameSurfaceRenderer(real_surface)

        # Begin frame
        renderer.begin_frame((0, 0, 0, 255))

        # Queue some commands
        renderer.fill((50, 50, 50))
        renderer.draw_line((255, 0, 0), (0, 0), (100, 100), width=2)
        renderer.draw_rect((0, 255, 0), pygame.Rect(200, 200, 100, 100))

        # Verify commands are queued
        assert len(renderer._command_queue) == 3

        # Update (execute commands)
        renderer.update()

        # Queue should be empty
        assert len(renderer._command_queue) == 0

        # Display should be updated
        mock_display_update.assert_called_once()

    @patch("pygame.display.update")
    def test_view_enqueue_and_renderer_update(self, mock_display_update, real_surface):
        """Test that view can enqueue and renderer can update."""
        renderer = PygameSurfaceRenderer(real_surface)
        view = renderer.view()

        # View queues commands
        view.fill((100, 100, 100))
        view.draw_line((255, 255, 0), (50, 50), (150, 150))

        # Renderer executes them
        renderer.update()

        assert len(renderer._command_queue) == 0
        mock_display_update.assert_called_once()

    @patch("pygame.display.update")
    def test_multiple_frames(self, mock_display_update, real_surface):
        """Test multiple frame cycles."""
        renderer = PygameSurfaceRenderer(real_surface)

        # Frame 1
        renderer.begin_frame()
        renderer.fill((255, 0, 0))
        renderer.update()
        assert len(renderer._command_queue) == 0

        # Frame 2
        renderer.begin_frame()
        renderer.fill((0, 255, 0))
        renderer.update()
        assert len(renderer._command_queue) == 0

        # Display updated twice
        assert mock_display_update.call_count == 2
