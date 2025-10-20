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

"""AssetsSystem - provides read-only access to game assets (fonts, sprites, sounds)."""

import pygame
from typing import Optional
from src.ecs.systems.base_system import BaseSystem
from src.ecs.world import World


class AssetsSystem(BaseSystem):
    """System that manages and provides read-only access to game assets.

    This system loads and caches game assets like fonts, sprites, and sounds.
    It provides a clean interface for other systems to access these assets
    without directly managing pygame resources.

    The interface is designed to be generic so that asset types can be swapped
    (e.g., from pixel art to realistic sprites) without changing other systems.

    Attributes:
        fonts: Dictionary of loaded fonts keyed by size/name
        sprites: Dictionary of loaded sprites
        sounds: Dictionary of loaded sound effects
    """

    # Asset file paths
    FONT_PATH = "assets/font/GetVoIP-Grotesque.ttf"
    SPEAKER_ON_SPRITE_PATH = "assets/sprites/speaker-on.png"
    SPEAKER_MUTED_SPRITE_PATH = "assets/sprites/speaker-muted.png"
    GAMEOVER_SOUND_PATH = "assets/sound/gameover.wav"
    EAT_SOUND_PATH = "assets/sound/eat.flac"

    def __init__(self, window_width: int):
        """Initialize the AssetsSystem.

        Args:
            window_width: Current game window width (used for font sizing)
        """
        self._window_width = window_width
        self._fonts: dict[str, pygame.font.Font] = {}
        self._sprites: dict[str, pygame.Surface] = {}
        self._sounds: dict[str, pygame.mixer.Sound] = {}
        self._load_all_assets()

    def _load_all_assets(self) -> None:
        """Load all game assets into memory."""
        self._load_fonts()
        self._load_sprites()
        self._load_sounds()

    def _load_fonts(self) -> None:
        """Load game fonts with sizes based on window width."""
        try:
            # Big font for titles
            self._fonts["big"] = pygame.font.Font(
                self.FONT_PATH, int(self._window_width / 8)
            )
            # Small font for UI elements
            self._fonts["small"] = pygame.font.Font(
                self.FONT_PATH, int(self._window_width / 20)
            )
        except Exception as e:
            print(f"Warning: Could not load custom fonts: {e}")
            # Fallback to default pygame font
            self._fonts["big"] = pygame.font.Font(None, int(self._window_width / 8))
            self._fonts["small"] = pygame.font.Font(None, int(self._window_width / 20))

    def _load_sprites(self) -> None:
        """Load sprite images."""
        try:
            self._sprites["speaker_on"] = pygame.image.load(self.SPEAKER_ON_SPRITE_PATH)
        except pygame.error as e:
            print(f"Warning: Could not load speaker-on sprite: {e}")
            self._sprites["speaker_on"] = None

        try:
            self._sprites["speaker_muted"] = pygame.image.load(
                self.SPEAKER_MUTED_SPRITE_PATH
            )
        except pygame.error as e:
            print(f"Warning: Could not load speaker-muted sprite: {e}")
            self._sprites["speaker_muted"] = None

    def _load_sounds(self) -> None:
        """Load sound effects."""
        try:
            self._sounds["gameover"] = pygame.mixer.Sound(self.GAMEOVER_SOUND_PATH)
        except pygame.error as e:
            print(f"Warning: Could not load gameover sound: {e}")
            self._sounds["gameover"] = None

        try:
            self._sounds["eat"] = pygame.mixer.Sound(self.EAT_SOUND_PATH)
        except pygame.error as e:
            print(f"Warning: Could not load eat sound: {e}")
            self._sounds["eat"] = None

    def get_font(self, size_name: str = "small") -> pygame.font.Font:
        """Get a font by size name.

        Args:
            size_name: Font size identifier ("big" or "small")

        Returns:
            pygame.font.Font: The requested font, or small font if not found
        """
        return self._fonts.get(size_name, self._fonts.get("small"))

    def get_custom_font(self, size_px: int) -> pygame.font.Font:
        """Get or create a font with custom size.

        Args:
            size_px: Font size in pixels

        Returns:
            pygame.font.Font: Font with requested size
        """
        cache_key = f"custom_{size_px}"

        if cache_key not in self._fonts:
            try:
                self._fonts[cache_key] = pygame.font.Font(self.FONT_PATH, size_px)
            except Exception as e:
                print(f"Warning: Could not create custom font: {e}")
                self._fonts[cache_key] = pygame.font.Font(None, size_px)

        return self._fonts[cache_key]

    def get_sprite(self, sprite_name: str) -> Optional[pygame.Surface]:
        """Get a sprite by name.

        Args:
            sprite_name: Name of the sprite to retrieve

        Returns:
            pygame.Surface or None: The sprite surface, or None if not loaded
        """
        return self._sprites.get(sprite_name)

    def get_sound(self, sound_name: str) -> Optional[pygame.mixer.Sound]:
        """Get a sound effect by name.

        Args:
            sound_name: Name of the sound to retrieve

        Returns:
            pygame.mixer.Sound or None: The sound object, or None if not loaded
        """
        return self._sounds.get(sound_name)

    def reload_fonts(self, new_window_width: int) -> None:
        """Reload fonts when window size changes.

        Args:
            new_window_width: New window width for font sizing
        """
        self._window_width = new_window_width
        # Clear cached fonts
        self._fonts.clear()
        # Reload with new sizes
        self._load_fonts()

    def update(self, world: World) -> None:
        """Update method required by BaseSystem.

        AssetsSystem is passive - it doesn't need per-frame updates.
        Assets are loaded on initialization and reloaded when needed.

        Args:
            world: Game world (unused for assets)
        """
        # Assets don't need per-frame updates
        pass
