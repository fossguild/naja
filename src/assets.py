#!/usr/bin/env python3
#
#   Copyright (c) 2023, Monaco F. J. <monaco@usp.br>
#
#   This file is part of KobraPy.
#
#   KobraPy is free software: you can redistribute it and/or modify
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


class GameAssets:
    """Manages loading and reloading of game assets (sounds, sprites, fonts)."""

    # Asset file paths
    BACKGROUND_MUSIC_PATH = "assets/sound/BoxCat_Games_CPU_Talk.ogg"
    DEATH_MUSIC_PATH = "assets/sound/death_song.wav"
    GAMEOVER_SOUND_PATH = "assets/sound/gameover.wav"
    EAT_SOUND = "assets/sound/eat.flac"
    SPEAKER_ON_SPRITE_PATH = "assets/sprites/speaker-on.png"
    SPEAKER_MUTED_SPRITE_PATH = "assets/sprites/speaker-muted.png"
    FONT_PATH = "assets/font/GetVoIP-Grotesque.ttf"

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

        # Load all assets
        self.load_all()

    def load_all(self) -> None:
        """Load all game assets (fonts, sprites, sounds)."""
        self.load_fonts()
        self.load_sprites()
        self.load_sounds()

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
        except pygame.error as e:
            print(f"Warning: Could not load death music: {e}")

    @staticmethod
    def play_background_music(loop: bool = True) -> None:
        """Switch back to background music.

        Args:
            loop: Whether to loop the background music
        """
        try:
            pygame.mixer.music.stop()
            pygame.mixer.music.load(GameAssets.BACKGROUND_MUSIC_PATH)
            pygame.mixer.music.play(-1 if loop else 0)
        except pygame.error as e:
            print(f"Warning: Could not load background music: {e}")
