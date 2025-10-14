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

"""
Defines the main menu and settings menu screens and their logic.
"""

import sys
import pygame

from src.state import GameState
from src.assets import GameAssets
from src.config import GameConfig
from src.settings import GameSettings
from src.constants import (
    ARENA_COLOR,
    MESSAGE_COLOR,
    SCORE_COLOR,
    GRID_COLOR,
    WINDOW_TITLE,
)


def _draw_settings_menu(
    state: GameState, assets: GameAssets, settings: GameSettings, selected_index: int
) -> None:
    """Draw the settings menu screen.

    Args:
        state: GameState instance
        assets: GameAssets instance
        settings: GameSettings instance
        selected_index: Currently selected menu item index
    """
    state.arena.fill(ARENA_COLOR)

    title = assets.render_custom("Settings", MESSAGE_COLOR, int(state.width / 10))
    title_rect = title.get_rect(center=(state.width / 2, state.height / 10))
    state.arena.blit(title, title_rect)

    # Spacing and scroll parameters
    visible_rows = int(state.height * 0.75 // (state.height * 0.07))
    top_index = max(0, selected_index - visible_rows + 3)
    padding_y = int(state.height * 0.20)
    row_h = int(state.height * 0.07)

    # Draw visible rows
    for draw_i, field_i in enumerate(range(top_index, len(settings.MENU_FIELDS))):
        if draw_i >= visible_rows:
            break
        f = settings.MENU_FIELDS[field_i]
        val = settings.get(f["key"])
        formatted_val = settings.format_setting_value(
            f, val, state.width, state.grid_size
        )
        text = assets.render_small(
            f"{f['label']}: {formatted_val}",
            SCORE_COLOR if field_i == selected_index else MESSAGE_COLOR,
        )
        rect = text.get_rect()
        rect.left = int(state.width * 0.12)
        rect.top = padding_y + draw_i * row_h
        state.arena.blit(text, rect)

    # Hint footer (smaller)
    hint_text = "[A/D] change   [W/S] select   [Enter/Esc] back"
    hint = assets.render_custom(hint_text, GRID_COLOR, int(state.width / 40))
    state.arena.blit(hint, hint.get_rect(center=(state.width / 2, state.height * 0.95)))

    pygame.display.update()


def run_settings_menu(
    state: GameState, assets: GameAssets, settings: GameSettings
) -> None:
    """Run the settings menu modal loop.

    Args:
        state: GameState instance
        assets: GameAssets instance
        settings: GameSettings instance
    """
    selected = 0

    while True:
        _draw_settings_menu(state, assets, settings, selected)

        for event in pygame.event.get():
            # Guard clauses keep nesting shallow.
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type != pygame.KEYDOWN:
                continue

            key = event.key

            if key in (pygame.K_ESCAPE, pygame.K_RETURN):
                return  # exit menu

            if key in (pygame.K_DOWN, pygame.K_s):
                selected = (selected + 1) % len(settings.MENU_FIELDS)
                continue

            if key in (pygame.K_UP, pygame.K_w):
                selected = (selected - 1) % len(settings.MENU_FIELDS)
                continue

            if key in (pygame.K_LEFT, pygame.K_a):
                settings.step_setting(settings.MENU_FIELDS[selected], -1)
                continue

            if key in (pygame.K_RIGHT, pygame.K_d):
                settings.step_setting(settings.MENU_FIELDS[selected], +1)
                continue


def start_menu(
    state: GameState,
    assets: GameAssets,
    config: GameConfig,
    settings: GameSettings,
    apply_settings_callback,
) -> None:
    """Main menu shown before the game starts.

    Args:
        state: GameState instance
        assets: GameAssets instance
        config: GameConfig instance
        settings: GameSettings instance
    """
    selected = 0
    items = ["Start Game", "Settings"]

    while True:
        state.arena.fill(ARENA_COLOR)

        # Title
        title = assets.render_big(WINDOW_TITLE, MESSAGE_COLOR)
        state.arena.blit(
            title, title.get_rect(center=(state.width / 2, state.height / 4))
        )

        # Draw buttons
        for i, text_label in enumerate(items):
            color = SCORE_COLOR if i == selected else MESSAGE_COLOR
            text = assets.render_small(text_label, color)
            rect = text.get_rect(
                center=(state.width / 2, state.height / 2 + i * (state.height * 0.12))
            )
            state.arena.blit(text, rect)

        pygame.display.update()

        # Input handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                key = event.key
                if key in (pygame.K_UP, pygame.K_w):
                    selected = (selected - 1) % len(items)
                elif key in (pygame.K_DOWN, pygame.K_s):
                    selected = (selected + 1) % len(items)
                elif key in (pygame.K_RETURN, pygame.K_SPACE):
                    if items[selected] == "Start Game":
                        return  # proceed to game
                    elif items[selected] == "Settings":
                        run_settings_menu(state, assets, settings)
                        apply_settings_callback(reset_objects=False)
                elif key == pygame.K_m:
                    run_settings_menu(state, assets, settings)
                    apply_settings_callback(reset_objects=False)
                elif key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # Simple click detection
                mx, my = event.pos
                for i, text_label in enumerate(items):
                    rect = assets.render_small(text_label, MESSAGE_COLOR).get_rect(
                        center=(
                            state.width / 2,
                            state.height / 2 + i * (state.height * 0.12),
                        )
                    )
                    if rect.collidepoint(mx, my):
                        if text_label == "Start Game":
                            return
                        elif text_label == "Settings":
                            run_settings_menu(state, assets, settings)
                            apply_settings_callback(reset_objects=False)
