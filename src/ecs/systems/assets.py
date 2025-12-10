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
from ecs.systems.base_system import BaseSystem
from ecs.world import World


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

    # Snake sprite paths
    SNAKE_HEAD_SPRITE_PATH = "assets/sprites/snake-head.png"
    SNAKE_BODY_SPRITE_PATH = "assets/sprites/snake-body.png"
    SNAKE_TURN_SPRITE_PATH = "assets/sprites/snake-turn.png"
    SNAKE_TAIL_SPRITE_PATH = "assets/sprites/snake-tail.png"

    def __init__(self, window_width: int):
        """Initialize the AssetsSystem.

        Args:
            window_width: Current game window width (used for font sizing)
        """
        self._window_width = window_width
        self._fonts: dict[str, pygame.font.Font] = {}
        self._sprites: dict[str, pygame.Surface] = {}
        self._sounds: dict[str, pygame.mixer.Sound] = {}
        self._tinted_cache: dict[tuple, pygame.Surface] = {}  # Cache for tinted sprites
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
        # UI sprites
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

        # Snake sprites
        snake_sprites = {
            "snake_head": self.SNAKE_HEAD_SPRITE_PATH,
            "snake_body": self.SNAKE_BODY_SPRITE_PATH,
            "snake_turn": self.SNAKE_TURN_SPRITE_PATH,
            "snake_tail": self.SNAKE_TAIL_SPRITE_PATH,
        }
        for name, path in snake_sprites.items():
            try:
                # Load with alpha channel and convert for performance
                sprite = pygame.image.load(path).convert_alpha()
                self._sprites[name] = sprite
            except pygame.error as e:
                print(f"Warning: Could not load {name} sprite: {e}")
                self._sprites[name] = None

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

    def get_snake_sprite(self, part: str) -> Optional[pygame.Surface]:
        """Get a snake sprite by part name.

        Args:
            part: Part name ("head", "body", "turn", or "tail")

        Returns:
            pygame.Surface or None: The sprite surface, or None if not loaded
        """
        return self._sprites.get(f"snake_{part}")

    def tint_sprite(
        self, sprite: pygame.Surface, color: tuple[int, int, int]
    ) -> pygame.Surface:
        """Apply color tint to a sprite for skin customization.

        Works best when base sprite is white/grayscale:
        - White pixels become the tint color
        - Gray pixels become darker versions of tint
        - Black pixels stay black (preserves outlines)

        Args:
            sprite: Base sprite surface to tint
            color: RGB color tuple to apply

        Returns:
            New tinted sprite surface
        """
        tinted = sprite.copy()
        # Create a colored overlay and multiply blend
        tinted.fill(color, special_flags=pygame.BLEND_MULT)
        return tinted

    def get_tinted_snake_sprite(
        self, part: str, color: tuple[int, int, int], cell_size: int = 0
    ) -> Optional[pygame.Surface]:
        """Get a tinted and scaled snake sprite (cached).

        Caches tinted sprites to avoid re-processing every frame.

        Args:
            part: Part name ("head", "body", "turn", or "tail")
            color: RGB color tuple for tinting
            cell_size: Target size to scale sprite to (0 = no scaling)

        Returns:
            Tinted (and optionally scaled) sprite, or None if unavailable
        """
        cache_key = (part, color, cell_size)

        if cache_key not in self._tinted_cache:
            base = self.get_snake_sprite(part)
            if base is None:
                return None

            # Tint the sprite
            tinted = self.tint_sprite(base, color)

            # Scale if cell_size specified
            if cell_size > 0:
                tinted = pygame.transform.scale(tinted, (cell_size, cell_size))

            self._tinted_cache[cache_key] = tinted

        return self._tinted_cache.get(cache_key)

    def clear_tint_cache(self) -> None:
        """Clear the tinted sprite cache.

        Call when skin colors change or window resizes.
        """
        self._tinted_cache.clear()

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
