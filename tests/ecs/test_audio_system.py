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

"""Audio system tests."""

import pytest
from dataclasses import dataclass, field
from typing import List
from unittest.mock import Mock, MagicMock, patch

from src.ecs.world import World
from src.ecs.board import Board
from src.ecs.systems.audio import AudioSystem


@dataclass
class AudioQueueEntity:
    """Simple audio queue entity for testing."""

    sfx_queue: List[str] = field(default_factory=list)


@dataclass
class MusicStateEntity:
    """Simple music state entity for testing."""

    enabled: bool = True
    current_track: str = "background"
    volume: float = 0.2
    is_playing: bool = False
    is_paused: bool = False


@pytest.fixture
def board():
    """Create a standard board for testing."""
    return Board(width=10, height=10, cell_size=30)


@pytest.fixture
def world(board):
    """Create a world with board."""
    return World(board)


@pytest.fixture
def mock_sound():
    """Create a mock pygame Sound object."""
    sound = Mock()
    sound.play = Mock(return_value=None)
    sound.set_volume = Mock(return_value=None)
    return sound


@pytest.fixture
def audio_system(mock_sound):
    """Create an AudioSystem with mock sounds."""
    sound_assets = {
        "eat": mock_sound,
        "death": mock_sound,
        "gameover": mock_sound,
    }

    music_tracks = {
        "background": "assets/sound/background.ogg",
        "death": "assets/sound/death.mp3",
    }

    return AudioSystem(
        sound_assets=sound_assets,
        music_tracks=music_tracks,
        default_volume=0.2,
    )


class TestAudioSystemInitialization:
    """Test AudioSystem initialization."""

    def test_system_created_successfully(self):
        """Test that AudioSystem can be initialized."""
        system = AudioSystem()
        assert system is not None

    def test_system_with_sound_assets(self, mock_sound):
        """Test AudioSystem with sound assets."""
        sound_assets = {"test": mock_sound}
        system = AudioSystem(sound_assets=sound_assets)

        assert "test" in system.get_available_sfx()

    def test_system_with_music_tracks(self):
        """Test AudioSystem with music tracks."""
        music_tracks = {"track1": "path/to/track1.ogg"}
        system = AudioSystem(music_tracks=music_tracks)

        assert "track1" in system.get_available_tracks()


class TestSFXPlayback:
    """Test sound effects playback."""

    def test_play_sfx_calls_sound_play(self, audio_system, mock_sound):
        """Test that playing SFX calls sound.play()."""
        result = audio_system.play_sfx("eat")

        assert result is True
        mock_sound.play.assert_called_once()

    def test_play_nonexistent_sfx_returns_false(self, audio_system):
        """Test playing non-existent sound returns False."""
        result = audio_system.play_sfx("nonexistent")

        assert result is False

    def test_play_multiple_sfx_simultaneously(self, audio_system, mock_sound):
        """Test playing multiple SFX (mixer channels)."""
        audio_system.play_sfx("eat")
        audio_system.play_sfx("death")
        audio_system.play_sfx("gameover")

        # each should have been played
        assert mock_sound.play.call_count == 3


class TestSFXQueue:
    """Test SFX queue processing."""

    def test_queue_sfx_adds_to_queue(self, world, audio_system):
        """Test queuing sound effect."""
        audio_queue = AudioQueueEntity()
        world.registry.add(audio_queue)

        audio_system.queue_sfx(world, "eat")

        assert "eat" in audio_queue.sfx_queue

    def test_queue_multiple_sfx(self, world, audio_system):
        """Test queuing multiple sound effects."""
        audio_queue = AudioQueueEntity()
        world.registry.add(audio_queue)

        audio_system.queue_sfx(world, "eat")
        audio_system.queue_sfx(world, "death")

        assert len(audio_queue.sfx_queue) == 2

    def test_process_sfx_queue_plays_all_sounds(
        self, world, audio_system, mock_sound
    ):
        """Test processing SFX queue plays all sounds."""
        audio_queue = AudioQueueEntity(sfx_queue=["eat", "death"])
        world.registry.add(audio_queue)

        audio_system._process_sfx_queue(world)

        assert mock_sound.play.call_count == 2

    def test_process_sfx_queue_clears_queue(self, world, audio_system):
        """Test processing SFX queue clears it."""
        audio_queue = AudioQueueEntity(sfx_queue=["eat", "death"])
        world.registry.add(audio_queue)

        audio_system._process_sfx_queue(world)

        assert len(audio_queue.sfx_queue) == 0


@patch("pygame.mixer.music")
class TestMusicControl:
    """Test music control functions."""

    def test_play_music_loads_and_plays(self, mock_music, world, audio_system):
        """Test playing music loads and starts playback."""
        music_state = MusicStateEntity()
        world.registry.add(music_state)

        result = audio_system.play_music(world, "background", loop=True)

        assert result is True
        mock_music.load.assert_called_once()
        mock_music.play.assert_called_once_with(-1)
        assert music_state.is_playing is True

    def test_play_nonexistent_track_returns_false(
        self, mock_music, world, audio_system
    ):
        """Test playing non-existent track returns False."""
        result = audio_system.play_music(world, "nonexistent")

        assert result is False
        mock_music.load.assert_not_called()

    def test_pause_music_pauses_playback(self, mock_music, world, audio_system):
        """Test pausing music."""
        music_state = MusicStateEntity(is_playing=True)
        world.registry.add(music_state)

        audio_system.pause_music(world)

        mock_music.pause.assert_called_once()
        assert music_state.is_paused is True

    def test_unpause_music_resumes_playback(self, mock_music, world, audio_system):
        """Test unpausing music."""
        music_state = MusicStateEntity(is_playing=True, is_paused=True)
        world.registry.add(music_state)

        audio_system.unpause_music(world)

        mock_music.unpause.assert_called_once()
        assert music_state.is_paused is False

    def test_stop_music_stops_playback(self, mock_music, world, audio_system):
        """Test stopping music."""
        music_state = MusicStateEntity(is_playing=True)
        world.registry.add(music_state)

        audio_system.stop_music(world)

        mock_music.stop.assert_called_once()
        assert music_state.is_playing is False

    def test_next_track_switches_music(self, mock_music, world, audio_system):
        """Test switching to next track."""
        music_state = MusicStateEntity(is_playing=True, current_track="background")
        world.registry.add(music_state)

        result = audio_system.next_track(world, "death")

        assert result is True
        mock_music.stop.assert_called_once()
        assert mock_music.load.call_count == 1


@patch("pygame.mixer.music")
class TestMusicEnabledFlag:
    """Test music enabled flag behavior."""

    def test_play_music_respects_disabled_flag(
        self, mock_music, world, audio_system
    ):
        """Test that music doesn't play when disabled."""
        music_state = MusicStateEntity(enabled=False)
        world.registry.add(music_state)

        result = audio_system.play_music(world, "background")

        assert result is False
        mock_music.load.assert_not_called()

    def test_set_music_enabled_pauses_music(
        self, mock_music, world, audio_system
    ):
        """Test disabling music pauses it."""
        music_state = MusicStateEntity(enabled=True, is_playing=True)
        world.registry.add(music_state)

        audio_system.set_music_enabled(world, False)

        assert music_state.enabled is False
        mock_music.pause.assert_called_once()

    def test_set_music_enabled_unpauses_music(
        self, mock_music, world, audio_system
    ):
        """Test enabling music unpauses it."""
        music_state = MusicStateEntity(enabled=False, is_playing=True, is_paused=True)
        world.registry.add(music_state)

        audio_system.set_music_enabled(world, True)

        assert music_state.enabled is True
        mock_music.unpause.assert_called_once()

    def test_get_music_enabled_returns_status(self, mock_music, world, audio_system):
        """Test getting music enabled status."""
        music_state = MusicStateEntity(enabled=False)
        world.registry.add(music_state)

        enabled = audio_system.get_music_enabled(world)

        assert enabled is False

    def test_get_music_enabled_defaults_to_true(
        self, mock_music, world, audio_system
    ):
        """Test music enabled defaults to True when no state exists."""
        enabled = audio_system.get_music_enabled(world)

        assert enabled is True


@patch("pygame.mixer.music")
class TestVolumeControl:
    """Test volume control."""

    def test_set_music_volume(self, mock_music, audio_system):
        """Test setting music volume."""
        audio_system.set_music_volume(0.5)

        mock_music.set_volume.assert_called_once_with(0.5)

    def test_set_music_volume_clamps_to_valid_range(self, mock_music, audio_system):
        """Test volume is clamped to 0.0-1.0."""
        audio_system.set_music_volume(1.5)
        mock_music.set_volume.assert_called_with(1.0)

        audio_system.set_music_volume(-0.5)
        mock_music.set_volume.assert_called_with(0.0)

    def test_set_sfx_volume(self, mock_music, audio_system, mock_sound):
        """Test setting SFX volume."""
        audio_system.set_sfx_volume("eat", 0.7)

        mock_sound.set_volume.assert_called_once_with(0.7)

    def test_set_sfx_volume_for_nonexistent_sound(
        self, mock_music, audio_system
    ):
        """Test setting volume for non-existent sound doesn't crash."""
        audio_system.set_sfx_volume("nonexistent", 0.5)
        # should not raise error


class TestSoundLoading:
    """Test loading sounds and music tracks."""

    @patch("pygame.mixer.Sound")
    def test_load_sound_successfully(self, mock_sound_class, audio_system):
        """Test loading sound from file."""
        mock_sound_instance = Mock()
        mock_sound_class.return_value = mock_sound_instance

        result = audio_system.load_sound("new_sfx", "path/to/sound.wav")

        assert result is True
        assert "new_sfx" in audio_system.get_available_sfx()

    @patch("pygame.mixer.Sound", side_effect=Exception("Load error"))
    def test_load_sound_handles_error(self, mock_sound_class, audio_system):
        """Test loading sound handles errors gracefully."""
        result = audio_system.load_sound("bad_sfx", "invalid/path.wav")

        assert result is False

    def test_load_music_track_registers_path(self, audio_system):
        """Test loading music track registers the path."""
        audio_system.load_music_track("new_track", "path/to/music.ogg")

        assert "new_track" in audio_system.get_available_tracks()


@patch("pygame.mixer.music")
class TestMusicStatus:
    """Test music status queries."""

    def test_is_music_playing(self, mock_music, audio_system):
        """Test checking if music is playing."""
        mock_music.get_busy.return_value = True

        result = audio_system.is_music_playing()

        assert result is True
        mock_music.get_busy.assert_called_once()


class TestAvailableAssets:
    """Test querying available assets."""

    def test_get_available_sfx_returns_list(self, audio_system):
        """Test getting list of available SFX."""
        sfx_list = audio_system.get_available_sfx()

        assert isinstance(sfx_list, list)
        assert "eat" in sfx_list
        assert "death" in sfx_list
        assert "gameover" in sfx_list

    def test_get_available_tracks_returns_list(self, audio_system):
        """Test getting list of available music tracks."""
        tracks_list = audio_system.get_available_tracks()

        assert isinstance(tracks_list, list)
        assert "background" in tracks_list
        assert "death" in tracks_list


@patch("pygame.mixer.music")
class TestIntegration:
    """Integration tests for AudioSystem."""

    def test_full_audio_workflow(self, mock_music, world, audio_system, mock_sound):
        """Test complete audio workflow."""
        # create entities
        audio_queue = AudioQueueEntity()
        music_state = MusicStateEntity()
        world.registry.add(audio_queue)
        world.registry.add(music_state)

        # start music
        audio_system.play_music(world, "background")
        assert music_state.is_playing is True

        # queue and play SFX
        audio_system.queue_sfx(world, "eat")
        audio_system._process_sfx_queue(world)
        assert len(audio_queue.sfx_queue) == 0
        mock_sound.play.assert_called()

        # pause music
        audio_system.pause_music(world)
        assert music_state.is_paused is True

        # unpause music
        audio_system.unpause_music(world)
        assert music_state.is_paused is False

        # switch track
        audio_system.next_track(world, "death")
        assert music_state.current_track == "death"

    def test_music_disabled_workflow(self, mock_music, world, audio_system):
        """Test audio with music disabled."""
        music_state = MusicStateEntity(enabled=False)
        world.registry.add(music_state)

        # music should not play
        result = audio_system.play_music(world, "background")
        assert result is False

        # enable music
        audio_system.set_music_enabled(world, True)
        assert music_state.enabled is True

        # now music can play
        result = audio_system.play_music(world, "background")
        assert result is True

    def test_multiple_sfx_with_music(
        self, mock_music, world, audio_system, mock_sound
    ):
        """Test playing multiple SFX while music plays."""
        music_state = MusicStateEntity()
        audio_queue = AudioQueueEntity()
        world.registry.add(music_state)
        world.registry.add(audio_queue)

        # start music
        audio_system.play_music(world, "background")

        # play multiple SFX simultaneously
        audio_system.queue_sfx(world, "eat")
        audio_system.queue_sfx(world, "death")
        audio_system.queue_sfx(world, "gameover")

        audio_system._process_sfx_queue(world)

        # all SFX should have played
        assert mock_sound.play.call_count == 3
        # music should still be playing
        assert music_state.is_playing is True

