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

"""Game over scene."""

from __future__ import annotations

import pygame
import sys
from typing import Optional
from datetime import datetime

from game.scenes.base_scene import BaseScene
from game.services.assets import GameAssets
from game.constants import (
    ARENA_PRIMARY_COLOR,
    GAME_OVER_MESSAGE_COLOR,
    GAME_OVER_HIGHLIGHT_COLOR,
    GAME_OVER_NEW_SCORE_COLOR,
    GAME_OVER_HIGH_SCORE_COLOR,
    GAME_OVER_TIMESTAMP_COLOR,
    GAME_OVER_TIMESTAMP_HIGHLIGHT_COLOR,
)
from game.scoreboard import Scoreboard, MAX_SCOREBOARD_ENTRIES
from game.settings import GameSettings
from game.game_modes_registry import GameModeType
from ecs.world import World


class GameOverScene(BaseScene):
    """Game over scene."""

    def __init__(
        self,
        pygame_adapter,
        renderer,
        width: int,
        height: int,
        assets: GameAssets,
        death_reason: str = "",
        settings: Optional[GameSettings] = None,
        scoreboard: Optional[Scoreboard] = None,
        world: Optional[World] = None,
    ):
        """Initialize the game over scene.

        Args:
            pygame_adapter: Pygame IO adapter
            renderer: Renderer for drawing
            width: Scene width
            height: Scene height
            assets: Game assets
            death_reason: Reason for game over
            settings: Optional GameSettings instance
            scoreboard: Optional Scoreboard instance
            world: Optional World instance to read final score from
            gamemode: Optional game mode identifier
        """
        super().__init__(pygame_adapter, renderer, width, height)
        self._assets = assets
        self._death_reason = death_reason
        self._settings = settings
        self._scoreboard = scoreboard
        self._world = world

        # Get gamemode from parameter or from world's game state component
        self._gamemode: GameModeType | None = None

        self._current_score = 0
        self._is_new_high_score = False
        self._new_score_timestamp = None

    def update(self, dt_ms: float) -> Optional[str]:
        """Update game over logic.

        Args:
            dt_ms: Delta time in milliseconds

        Returns:
            Next scene name or None
        """
        # Handle input
        for event in self._pygame_adapter.get_events():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    return "gameplay"  # restart game directly
                elif event.key == pygame.K_q:
                    return "menu"  # return to main menu

        return None

    def render(self) -> None:
        """Render the game over screen."""
        # Clear screen with arena color
        self._renderer.fill(ARENA_PRIMARY_COLOR)

        # Draw game over text and scores
        try:
            # calculate font sizes
            big_font_size = int(self._width / 8)
            medium_font_size = int(self._width / 20)
            small_font_size = int(self._width / 25)
            tiny_font_size = int(self._width / 45)  # Even smaller for timestamps

            # create fonts with same font file and sizing as old code
            font_path = "assets/font/GetVoIP-Grotesque.ttf"

            try:
                # try to load the same font as old code
                big_font = pygame.font.Font(font_path, big_font_size)
                medium_font = pygame.font.Font(font_path, medium_font_size)
                small_font = pygame.font.Font(font_path, small_font_size)
                tiny_font = pygame.font.Font(font_path, tiny_font_size)
            except Exception:
                # fallback to default font if GetVoIP font not found
                big_font = pygame.font.Font(None, big_font_size)
                medium_font = pygame.font.Font(None, medium_font_size)
                small_font = pygame.font.Font(None, small_font_size)
                tiny_font = pygame.font.Font(None, tiny_font_size)

            # Use color constants from game.constants
            message_color = GAME_OVER_MESSAGE_COLOR
            highlight_color = GAME_OVER_HIGHLIGHT_COLOR
            new_score_color = GAME_OVER_NEW_SCORE_COLOR
            high_score_color = GAME_OVER_HIGH_SCORE_COLOR

            # "Game Over" text centered
            game_over_text = big_font.render("Game Over", True, message_color)
            game_over_rect = game_over_text.get_rect(
                center=(self._width // 2, self._height / 5)
            )
            self._renderer.blit(game_over_text, game_over_rect)

            # Display "NEW HIGH SCORE!" if applicable
            y_offset = self._height / 3.5
            if self._is_new_high_score:
                high_score_text = medium_font.render(
                    "* NEW HIGH SCORE! *", True, high_score_color
                )
                high_score_rect = high_score_text.get_rect(
                    center=(self._width // 2, y_offset)
                )
                self._renderer.blit(high_score_text, high_score_rect)
                y_offset += 50

            # Display current score
            score_text = medium_font.render(
                f"Your Score: {self._current_score}", True, highlight_color
            )
            score_rect = score_text.get_rect(center=(self._width // 2, y_offset))
            self._renderer.blit(score_text, score_rect)

            # Display top scores for current settings
            if self._scoreboard and self._settings:
                y_offset += 100  # Increased spacing before high scores section
                highscores_title = small_font.render(
                    f"Top {MAX_SCOREBOARD_ENTRIES} Scores (Current Settings):",
                    True,
                    message_color,
                )
                highscores_rect = highscores_title.get_rect(
                    center=(self._width // 2, y_offset)
                )
                self._renderer.blit(highscores_title, highscores_rect)

                # Get sorted scores for current settings
                sorted_scores = self._scoreboard.sorted_scores(
                    self._settings, self._gamemode
                )
                # Take top entries oldest first
                top_scores = (
                    sorted_scores[:MAX_SCOREBOARD_ENTRIES]
                    if len(sorted_scores) >= MAX_SCOREBOARD_ENTRIES
                    else sorted_scores
                )

                # Display each score
                y_offset += 55  # Increased spacing after title
                for i, score_entry in enumerate(top_scores, 1):
                    score_value = score_entry["value"]
                    timestamp = score_entry["timestamp"]

                    # Check if this is the new score (by timestamp match)
                    # Only highlight if the player actually scored points
                    is_new_score = (
                        self._current_score > 0
                        and self._new_score_timestamp is not None
                        and isinstance(timestamp, datetime)
                        and abs((timestamp - self._new_score_timestamp).total_seconds())
                        < 1
                    )

                    # Format timestamp with seconds
                    if isinstance(timestamp, datetime):
                        time_str = timestamp.strftime(
                            "%d/%m/%Y %H:%M:%S"
                        )  # MM/DD HH:MM:SS
                    else:
                        time_str = str(timestamp)

                    # Choose color and prefix based on whether this is the new score
                    if is_new_score:
                        color = new_score_color
                        prefix = "* "
                    else:
                        color = message_color
                        prefix = "  "

                    # Render score line with rank and value (centered)
                    score_text = f"{prefix}{i}: {score_value}"
                    score_line = small_font.render(score_text, True, color)

                    # Render timestamp (to the right of score)
                    timestamp_color = (
                        GAME_OVER_TIMESTAMP_HIGHLIGHT_COLOR
                        if is_new_score
                        else GAME_OVER_TIMESTAMP_COLOR
                    )
                    timestamp_line = tiny_font.render(
                        f"  {time_str}", True, timestamp_color
                    )

                    # Center the score part, timestamp follows to the right
                    # This keeps scores aligned even with varying timestamp widths
                    score_x = (self._width - score_line.get_width()) // 2
                    timestamp_x = score_x + score_line.get_width()

                    # Blit score and timestamp
                    self._renderer.blit(score_line, (score_x, y_offset))
                    self._renderer.blit(timestamp_line, (timestamp_x, y_offset))

                    y_offset += 40  # Reduced spacing since timestamp is on same line

                # Add some spacing if there are fewer scores than max
                if len(top_scores) < MAX_SCOREBOARD_ENTRIES:
                    y_offset += 40 * (MAX_SCOREBOARD_ENTRIES - len(top_scores))

            # "Press Enter/Space to restart • Q to menu" text at bottom
            restart_text = small_font.render(
                "Press Enter/Space to play again • Q to menu", True, message_color
            )
            restart_rect = restart_text.get_rect(
                center=(self._width // 2, self._height - 50)
            )
            self._renderer.blit(restart_text, restart_rect)

        except Exception as e:
            # if font loading fails, just show arena color
            print(f"Error rendering game over screen: {e}")
            pass

    def on_enter(self) -> None:
        """Called when entering game over."""
        # Get final score from world's GameState component
        if self._world:
            game_state_entities = self._world.registry.query_by_component("game_state")
            if game_state_entities:
                entity = next(iter(game_state_entities.values()))
                if hasattr(entity, "game_state"):
                    self._current_score = entity.game_state.final_score
                    self._gamemode = entity.game_state.game_mode

        # Check if this is a new high score and capture timestamp
        # Note: The score has already been added to the scoreboard by ScoringSystem
        self._is_new_high_score = False
        if self._scoreboard and self._settings and self._current_score > 0:
            sorted_scores = self._scoreboard.sorted_scores(
                self._settings, self._gamemode
            )

            # Find all entries with the current score value
            matching_scores = [
                s for s in sorted_scores if s["value"] == self._current_score
            ]

            if matching_scores:
                self._new_score_timestamp = matching_scores[-1]["timestamp"]

                if sorted_scores:
                    highest_score = sorted_scores[0]["value"]
                    if (
                        self._current_score == highest_score
                        and self._new_score_timestamp == sorted_scores[0]["timestamp"]
                    ):
                        self._is_new_high_score = True

        # Play death song (like old code) - only if audio is not muted
        if not self._settings or self._settings.get("background_music"):
            try:
                from game.services.audio_service import AudioService
                from game.services.assets import GameAssets

                pygame.mixer.music.load("assets/sound/death_song.mp3")
                pygame.mixer.music.play(-1)  # loop
                # update trackers to prevent audio service from reloading the same track
                AudioService._current_music_track = "assets/sound/death_song.mp3"
                GameAssets._current_music_track = "assets/sound/death_song.mp3"
            except Exception:
                pass

    def on_exit(self) -> None:
        """Called when exiting game over."""
        # Stop death song
        try:
            from game.services.audio_service import AudioService
            from game.services.assets import GameAssets

            pygame.mixer.music.stop()
            # clear trackers so background music can start when returning to menu/gameplay
            AudioService._current_music_track = None
            GameAssets._current_music_track = None
        except Exception:
            pass
