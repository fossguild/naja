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

"""Unit tests for AssetsSystem."""

import pytest
import pygame
from unittest.mock import patch, MagicMock
from src.ecs.systems.assets import AssetsSystem
from src.ecs.world import World
from src.ecs.board import Board


@pytest.fixture(scope="module")
def pygame_init():
    """Initialize pygame once for all tests."""
    pygame.init()
    pygame.font.init()
    pygame.mixer.init()
    yield
    pygame.quit()


@pytest.fixture
def window_width():
    """Provide a standard window width for tests."""
    return 800


@pytest.fixture
def assets_system(pygame_init, window_width):
    """Provide a fresh AssetsSystem instance for each test."""
    return AssetsSystem(window_width)


@pytest.fixture
def world():
    """Provide a World instance for tests."""
    board = Board(10, 10)
    return World(board)


class TestAssetsSystemInitialization:
    """Tests for AssetsSystem initialization."""

    def test_initialization(self, assets_system):
        """Test that AssetsSystem initializes correctly."""
        assert isinstance(assets_system._fonts, dict)
        assert isinstance(assets_system._sprites, dict)
        assert isinstance(assets_system._sounds, dict)

    def test_fonts_loaded(self, assets_system):
        """Test that fonts are loaded on initialization."""
        assert "big" in assets_system._fonts
        assert "small" in assets_system._fonts
        assert isinstance(assets_system._fonts["big"], pygame.font.Font)
        assert isinstance(assets_system._fonts["small"], pygame.font.Font)

    def test_inherits_from_base_system(self, assets_system):
        """Test that AssetsSystem inherits from BaseSystem."""
        from src.ecs.systems.base_system import BaseSystem
        assert isinstance(assets_system, BaseSystem)


class TestFontManagement:
    """Tests for font loading and management."""

    def test_font_sizes_based_on_window_width(self, window_width):
        """Test that font sizes are calculated based on window width."""
        pygame.init()
        pygame.font.init()
        assets = AssetsSystem(window_width)

        big_font = assets.get_font("big")
        small_font = assets.get_font("small")

        # Verify fonts exist and are Font instances
        assert isinstance(big_font, pygame.font.Font)
        assert isinstance(small_font, pygame.font.Font)

    def test_get_font_returns_requested_font(self, assets_system):
        """Test that get_font returns the correct font."""
        big_font = assets_system.get_font("big")
        small_font = assets_system.get_font("small")

        assert big_font is assets_system._fonts["big"]
        assert small_font is assets_system._fonts["small"]

    def test_get_font_defaults_to_small(self, assets_system):
        """Test that get_font returns small font for unknown size."""
        unknown_font = assets_system.get_font("unknown_size")
        assert unknown_font is assets_system._fonts["small"]

    def test_get_font_default_parameter(self, assets_system):
        """Test that get_font defaults to small when no parameter given."""
        default_font = assets_system.get_font()
        assert default_font is assets_system._fonts["small"]

    def test_get_custom_font_creates_and_caches(self, assets_system):
        """Test that get_custom_font creates and caches custom sizes."""
        custom_size = 50
        font1 = assets_system.get_custom_font(custom_size)

        assert isinstance(font1, pygame.font.Font)

        cache_key = f"custom_{custom_size}"
        assert cache_key in assets_system._fonts

        # Calling again should return the same instance (cached)
        font2 = assets_system.get_custom_font(custom_size)
        assert font1 is font2

    def test_get_custom_font_different_sizes(self, assets_system):
        """Test that different custom font sizes are cached separately."""
        font_30 = assets_system.get_custom_font(30)
        font_60 = assets_system.get_custom_font(60)

        assert font_30 is not font_60
        assert "custom_30" in assets_system._fonts
        assert "custom_60" in assets_system._fonts

    def test_multiple_custom_fonts_are_cached(self, assets_system):
        """Test that multiple custom font sizes can be cached simultaneously."""
        sizes = [20, 30, 40, 50, 60]
        fonts = {size: assets_system.get_custom_font(size) for size in sizes}

        # All should be cached
        for size in sizes:
            cache_key = f"custom_{size}"
            assert cache_key in assets_system._fonts

        # All should be different instances
        font_instances = list(fonts.values())
        for i, font1 in enumerate(font_instances):
            for j, font2 in enumerate(font_instances):
                if i != j:
                    assert font1 is not font2


class TestFontReloading:
    """Tests for font reloading functionality."""

    def test_reload_fonts_clears_and_reloads(self, pygame_init):
        """Test that reload_fonts clears cache and reloads fonts."""
        assets = AssetsSystem(800)

        # Get initial fonts
        initial_big = assets.get_font("big")
        initial_small = assets.get_font("small")

        # Create a custom font to ensure cache is cleared
        assets.get_custom_font(50)
        assert "custom_50" in assets._fonts

        # Reload with new window width
        new_width = 1200
        assets.reload_fonts(new_width)

        # Custom fonts should be cleared
        assert "custom_50" not in assets._fonts

        # Standard fonts should be reloaded
        assert "big" in assets._fonts
        assert "small" in assets._fonts

        # Fonts should be new instances
        new_big = assets.get_font("big")
        new_small = assets.get_font("small")

        assert initial_big is not new_big
        assert initial_small is not new_small
        assert assets._window_width == new_width

    def test_reload_fonts_updates_sizes(self, pygame_init):
        """Test that reload_fonts changes font sizes based on new width."""
        assets = AssetsSystem(400)  # Small window
        small_window_font = assets.get_font("big")
        small_height = small_window_font.get_height()

        # Reload with larger window
        assets.reload_fonts(1600)  # Large window
        large_window_font = assets.get_font("big")
        large_height = large_window_font.get_height()

        # Larger window should have larger fonts
        assert large_height > small_height


class TestSpriteManagement:
    """Tests for sprite loading and access."""

    def test_get_sprite_returns_sprite_or_none(self, assets_system):
        """Test that get_sprite returns sprite or None."""
        sprite = assets_system.get_sprite("speaker_on")

        # Should return either a Surface or None
        if sprite is not None:
            assert isinstance(sprite, pygame.Surface)

    def test_get_sprite_unknown_returns_none(self, assets_system):
        """Test that get_sprite returns None for unknown sprites."""
        sprite = assets_system.get_sprite("unknown_sprite")
        assert sprite is None

    def test_sprite_loading_handles_missing_files(self, assets_system):
        """Test that sprite loading handles missing files gracefully."""
        # Even if sprite files don't exist, system should initialize
        assert "speaker_on" in assets_system._sprites
        assert "speaker_muted" in assets_system._sprites


class TestSoundManagement:
    """Tests for sound loading and access."""

    def test_get_sound_returns_sound_or_none(self, assets_system):
        """Test that get_sound returns sound or None."""
        sound = assets_system.get_sound("gameover")

        # Should return either a Sound or None
        if sound is not None:
            assert isinstance(sound, pygame.mixer.Sound)

    def test_get_sound_unknown_returns_none(self, assets_system):
        """Test that get_sound returns None for unknown sounds."""
        sound = assets_system.get_sound("unknown_sound")
        assert sound is None

    def test_sound_loading_handles_missing_files(self, assets_system):
        """Test that sound loading handles missing files gracefully."""
        # Even if sound files don't exist, system should initialize
        assert "gameover" in assets_system._sounds
        assert "eat" in assets_system._sounds


class TestSystemBehavior:
    """Tests for system behavior and integration."""

    def test_update_does_nothing(self, assets_system, world):
        """Test that update method is a no-op (passive system)."""
        # Should not raise any exceptions
        assets_system.update(world)

    @patch('pygame.font.Font')
    def test_font_loading_fallback_on_error(self, mock_font, pygame_init):
        """Test that font loading falls back to default on error."""
        def font_side_effect(path, size):
            if path is not None and "GetVoIP" in path:
                raise Exception("Font file not found")
            return MagicMock()

        mock_font.side_effect = font_side_effect

        # Should not raise exception, should fallback to default font
        assets = AssetsSystem(800)

        # Should still have fonts (fallback fonts)
        assert "big" in assets._fonts
        assert "small" in assets._fonts
