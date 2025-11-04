#!/usr/bin/env python3
#
#   Copyright (c) 2023, Monaco F. J. <monaco@usp.br>
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

"""Audio service for managing game audio playback.

This service provides a high-level interface for playing sounds and music,
respecting the user's audio settings. It centralizes all audio logic that
would otherwise be scattered across scenes and systems.
"""

import pygame


class AudioService:
    """Service for managing game audio (music and sound effects).

    This service:
    - Provides a clean interface for playing sounds and music
    - Respects user settings (background_music, sound_effects)
    - Handles audio errors gracefully (missing files, etc.)
    - Centralizes audio logic in one place

    Architecture note: While we have an AudioSystem for ECS-based audio,
    this service is needed for scene-level audio control (background music,
    UI sounds, etc.) that don't fit well into the ECS update loop.
    """

    def __init__(self, settings=None):
        """Initialize the audio service.

        Args:
            settings: Game settings object with audio preferences
        """
        self._settings = settings

    def play_sound(self, sound_path: str, volume: float = 1.0) -> bool:
        """Play a sound effect if sound effects are enabled.

        Args:
            sound_path: Path to sound file (relative to project root)
            volume: Volume level (0.0 to 1.0), defaults to 1.0 (full volume)

        Returns:
            True if sound was played, False otherwise
        """
        # Check if sound effects are enabled
        if not self._settings or not self._settings.get("sound_effects"):
            return False

        try:
            sound = pygame.mixer.Sound(sound_path)
            # Clamp volume to valid range (0.0 to 1.0)
            volume = max(0.0, min(1.0, volume))
            sound.set_volume(volume)
            sound.play()
            return True
        except Exception:
            # Silently ignore missing files or playback errors
            return False

    def play_music(self, music_path: str, loop: bool = True) -> bool:
        """Play background music if music is enabled.

        Args:
            music_path: Path to music file (relative to project root)
            loop: Whether to loop the music (-1 for infinite loop)

        Returns:
            True if music was started, False otherwise
        """
        # Check if background music is enabled
        if not self._settings or not self._settings.get("background_music"):
            return False

        try:
            pygame.mixer.music.load(music_path)
            pygame.mixer.music.play(-1 if loop else 0)
            return True
        except Exception:
            # Silently ignore missing files or playback errors
            return False

    def pause_music(self) -> None:
        """Pause background music."""
        try:
            pygame.mixer.music.pause()
        except Exception:
            pass

    def unpause_music(self) -> None:
        """Unpause background music."""
        try:
            pygame.mixer.music.unpause()
        except Exception:
            pass

    def stop_music(self) -> None:
        """Stop background music."""
        try:
            pygame.mixer.music.stop()
        except Exception:
            pass

    def toggle_all_audio(self) -> bool:
        """Toggle all audio (music + sound effects) on/off.

        Returns:
            New audio state (True = enabled, False = disabled)
        """
        if not self._settings:
            return False

        # Get current state
        current_music = self._settings.get("background_music")
        current_sfx = self._settings.get("sound_effects")

        # If either is on, turn both off. If both are off, turn both on.
        new_state = not (current_music or current_sfx)

        # Update settings
        self._settings.set("background_music", new_state)
        self._settings.set("sound_effects", new_state)

        # Apply immediately
        if new_state:
            self._unmute_audio()
        else:
            self._mute_audio()

        return new_state

    def _mute_audio(self) -> None:
        """Mute all audio (internal helper)."""
        try:
            pygame.mixer.music.pause()
            pygame.mixer.pause()  # Pause all sound effect channels
        except Exception:
            pass

    def _unmute_audio(self) -> None:
        """Unmute all audio (internal helper)."""
        try:
            # Try to unpause music first
            pygame.mixer.music.unpause()

            # If music isn't playing, try to reload and play background music
            if not pygame.mixer.music.get_busy():
                try:
                    pygame.mixer.music.load("assets/sound/BoxCat_Games_CPU_Talk.ogg")
                    pygame.mixer.music.play(-1)
                except Exception:
                    pass

            # Unpause all sound effect channels
            pygame.mixer.unpause()
        except Exception:
            pass

    def is_music_playing(self) -> bool:
        """Check if music is currently playing.

        Returns:
            True if music is playing, False otherwise
        """
        try:
            return pygame.mixer.music.get_busy()
        except Exception:
            return False
