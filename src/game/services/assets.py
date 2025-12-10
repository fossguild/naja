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

import pygame
from typing import Optional


class GameAssets:
    """Manages loading and reloading of game assets (sounds, sprites, fonts)."""

    # Asset file paths
    BACKGROUND_MUSIC_PATH = "assets/sound/Slither_Sprint.mp3"
    DEATH_MUSIC_PATH = "assets/sound/death_song.mp3"
    GAMEOVER_SOUND_PATH = "assets/sound/gameover.wav"
    EAT_SOUND = "assets/sound/eat.flac"
    SPEAKER_ON_SPRITE_PATH = "assets/sprites/speaker-on.png"
    SPEAKER_MUTED_SPRITE_PATH = "assets/sprites/speaker-muted.png"
    FONT_PATH = "assets/font/LilitaOne-Regular.ttf"
    BUTTON_PATH = "assets/buttons/"
    SNAKE_ICONS_PATH = "assets/snake-icons"

    # Snake sprite paths
    SNAKE_SPRITE_PATH = "assets/sprites"
    SNAKE_HEAD_SPRITE = "snake-head.png"
    SNAKE_BODY_SPRITE = "snake-body.png"
    SNAKE_TURN_SPRITE = "snake-turn.png"
    SNAKE_TAIL_SPRITE = "snake-tail.png"

    # track currently loaded music to avoid unnecessary reloads
    _current_music_track = None

    def __init__(self, window_width: int):
        """Initialize and load all game assets.

        Args:
            window_width: Current game window width (used for font sizing)
        """
        self.window_width = window_width

        # Font assets
        self.big_font = None
        self.small_font = None

        # Sprite assets
        self.speaker_on_sprite = None
        self.speaker_muted_sprite = None

        # Sound assets
        self.gameover_sound = None
        self.eat_sound = None

        # Snake sprite assets
        self.snake_sprites: dict[str, Optional[pygame.Surface]] = {}
        self._tinted_cache: dict[tuple, pygame.Surface] = {}

        # Load all assets
        self.load_all()

    def load_all(self) -> None:
        """Load all game assets (fonts, sprites, sounds)."""
        self.load_fonts()
        self.load_sprites()
        self.load_sounds()
        self.load_buttons()
        self.load_snake_icons()
        self.load_snake_sprites()

    def load_fonts(self) -> None:
        """Load game fonts with sizes based on window width."""
        try:
            self.big_font = pygame.font.Font(self.FONT_PATH, int(self.window_width / 8))
            self.small_font = pygame.font.Font(
                self.FONT_PATH, int(self.window_width / 20)
            )
        except Exception as e:
            print(f"Error loading fonts: {e}")
            # Fallback to default font
            self.big_font = pygame.font.Font(None, int(self.window_width / 8))
            self.small_font = pygame.font.Font(None, int(self.window_width / 20))

    def load_sprites(self) -> None:
        """Load sprite images."""
        try:
            self.speaker_on_sprite = pygame.image.load(self.SPEAKER_ON_SPRITE_PATH)
        except pygame.error as e:
            print(f"Warning: Could not load speaker-on sprite: {e}")
            self.speaker_on_sprite = None

        try:
            self.speaker_muted_sprite = pygame.image.load(
                self.SPEAKER_MUTED_SPRITE_PATH
            )
        except pygame.error as e:
            print(f"Warning: Could not load speaker-muted sprite: {e}")
            self.speaker_muted_sprite = None

    def load_sounds(self) -> None:
        """Load sound effects."""
        try:
            self.gameover_sound = pygame.mixer.Sound(self.GAMEOVER_SOUND_PATH)
        except pygame.error as e:
            print(f"Warning: Could not load gameover sound: {e}")
            self.gameover_sound = None

        try:
            self.eat_sound = pygame.mixer.Sound(self.EAT_SOUND)
        except pygame.error as e:
            print(f"Warning: Could not load eat sound: {e}")
            self.eat_sound = None

    def load_snake_icons(self) -> None:
        """Load snake icons (used on selected text)"""
        try:
            self.snake_icons_left = pygame.image.load(
                f"{self.SNAKE_ICONS_PATH}/snake-icons-left.png",
            )
        except pygame.error as e:
            print(f"Warning: Could not load snake icon (left): {e}")
            self.snake_icons_left = None
        try:
            self.snake_icons_right = pygame.image.load(
                f"{self.SNAKE_ICONS_PATH}/snake-icons-right.png",
            )
        except pygame.error as e:
            print(f"Warning: Could not load snake icon (right): {e}")
            self.snake_icons_right = None

    def load_snake_sprites(self) -> None:
        """Load snake sprites for sprite-based rendering."""
        sprite_files = {
            "head": self.SNAKE_HEAD_SPRITE,
            "body": self.SNAKE_BODY_SPRITE,
            "turn": self.SNAKE_TURN_SPRITE,
            "tail": self.SNAKE_TAIL_SPRITE,
        }
        for part, filename in sprite_files.items():
            try:
                path = f"{self.SNAKE_SPRITE_PATH}/{filename}"
                sprite = pygame.image.load(path).convert_alpha()
                self.snake_sprites[part] = sprite
            except pygame.error as e:
                print(f"Warning: Could not load snake {part} sprite: {e}")
                self.snake_sprites[part] = None

    def get_snake_sprite(self, part: str) -> Optional[pygame.Surface]:
        """Get a snake sprite by part name.

        Args:
            part: Part name ("head", "body", "turn", or "tail")

        Returns:
            pygame.Surface or None: The sprite surface, or None if not loaded
        """
        return self.snake_sprites.get(part)

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

    def load_buttons(self) -> None:
        """Load button images"""
        try:
            self.button_start = pygame.image.load(
                f"{self.BUTTON_PATH}/start.png",
            )
        except pygame.error as e:
            print(f"Warning: Could not load start button: {e}")
            self.button_start = None
        try:
            self.button_start_hover = pygame.image.load(
                f"{self.BUTTON_PATH}/start_hover.png",
            )
        except pygame.error as e:
            print(f"Warning: Could not load start hover button: {e}")
            self.button_start_hover = None

        try:
            self.button_gamemode = pygame.image.load(
                f"{self.BUTTON_PATH}/gamemode.png",
            )
        except pygame.error as e:
            print(f"Warning: Could not load game mode button: {e}")
            self.button_gamemode = None
        try:
            self.button_gamemode_hover = pygame.image.load(
                f"{self.BUTTON_PATH}/gamemode_hover.png",
            )
        except pygame.error as e:
            print(f"Warning: Could not load game mode hover button: {e}")
            self.button_gamemode_hover = None

        try:
            self.button_settings = pygame.image.load(
                f"{self.BUTTON_PATH}/settings.png",
            )
        except pygame.error as e:
            print(f"Warning: Could not load settings button: {e}")
            self.button_settings = None
        try:
            self.button_settings_hover = pygame.image.load(
                f"{self.BUTTON_PATH}/settings_hover.png",
            )
        except pygame.error as e:
            print(f"Warning: Could not load settings hover button: {e}")
            self.button_settings_hover = None

        try:
            self.button_quit = pygame.image.load(
                f"{self.BUTTON_PATH}/quit.png",
            )
        except pygame.error as e:
            print(f"Warning: Could not load quit button: {e}")
            self.button_quit = None
        try:
            self.button_quit_hover = pygame.image.load(
                f"{self.BUTTON_PATH}/quit_hover.png",
            )
        except pygame.error as e:
            print(f"Warning: Could not load quit hover button : {e}")
            self.button_quit_hover = None

    def reload_fonts(self, new_window_width: int) -> None:
        """Reload fonts with new window width.

        Args:
            new_window_width: New window width for font sizing
        """
        self.window_width = new_window_width
        self.load_fonts()

    def reload_all(self, new_window_width: int = None) -> None:
        """Reload all game assets.

        Args:
            new_window_width: Optional new window width for font sizing
        """
        if new_window_width is not None:
            self.window_width = new_window_width
        self.load_all()

    def render_big(self, text: str, color, antialias: bool = True):
        """Render text using the big font.

        Args:
            text: Text to render
            color: Text color
            antialias: Whether to use antialiasing (default: True)

        Returns:
            Rendered text surface
        """
        return self.big_font.render(text, antialias, color)

    def render_small(self, text: str, color, antialias: bool = True):
        """Render text using the small font.

        Args:
            text: Text to render
            color: Text color
            antialias: Whether to use antialiasing (default: True)

        Returns:
            Rendered text surface
        """
        return self.small_font.render(text, antialias, color)

    def render_custom(self, text: str, color, size_px: int, antialias: bool = True):
        """Render text using a custom font size.

        Args:
            text: Text to render
            color: Text color
            size_px: Font size in pixels
            antialias: Whether to use antialiasing (default: True)

        Returns:
            Rendered text surface
        """
        try:
            custom_font = pygame.font.Font(self.FONT_PATH, size_px)
            return custom_font.render(text, antialias, color)
        except Exception as e:
            print(f"Error creating custom font: {e}")
            fallback_font = pygame.font.Font(None, size_px)
            return fallback_font.render(text, antialias, color)

    @staticmethod
    def init_music(volume: float = 0.2, start_playing: bool = True) -> None:
        """Initialize and start background music.

        Args:
            volume: Music volume (0.0 to 1.0)
            start_playing: Whether to start playing immediately
        """
        try:
            pygame.mixer.music.load(GameAssets.BACKGROUND_MUSIC_PATH)
            pygame.mixer.music.set_volume(volume)
            if start_playing:
                pygame.mixer.music.play(-1)  # Loop forever
            GameAssets._current_music_track = GameAssets.BACKGROUND_MUSIC_PATH
        except pygame.error as e:
            print(f"Warning: Could not load background music: {e}")

    @staticmethod
    def play_death_music(loop: bool = True) -> None:
        """Switch to death music.

        Args:
            loop: Whether to loop the death music
        """
        try:
            pygame.mixer.music.stop()
            pygame.mixer.music.load(GameAssets.DEATH_MUSIC_PATH)
            pygame.mixer.music.play(-1 if loop else 0)
            GameAssets._current_music_track = GameAssets.DEATH_MUSIC_PATH
        except pygame.error as e:
            print(f"Warning: Could not load death music: {e}")

    @staticmethod
    def play_background_music(loop: bool = True) -> None:
        """Switch back to background music.

        Args:
            loop: Whether to loop the background music
        """
        try:
            # only reload if the background music is not already the current track
            # this prevents resetting the track when transitioning between menu screens
            if GameAssets._current_music_track != GameAssets.BACKGROUND_MUSIC_PATH:
                pygame.mixer.music.load(GameAssets.BACKGROUND_MUSIC_PATH)
                pygame.mixer.music.play(-1 if loop else 0)
                GameAssets._current_music_track = GameAssets.BACKGROUND_MUSIC_PATH
        except pygame.error as e:
            print(f"Warning: Could not load background music: {e}")
