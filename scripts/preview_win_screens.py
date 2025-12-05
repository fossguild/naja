#!/usr/bin/env python3
"""Preview all victory screens for testing purposes.

Run with: .venv/bin/python scripts/preview_win_screens.py
"""

import pygame
import sys
import os

# Add src to path - must be before imports
src_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
sys.path.insert(0, src_path)

from game.constants import (  # noqa: E402
    ARENA_PRIMARY_COLOR,
    VICTORY_TITLE_COLOR,
    VICTORY_MESSAGE_COLOR,
    VICTORY_HIGHLIGHT_COLOR,
    VICTORY_HIGH_SCORE_COLOR,
    GAME_OVER_MESSAGE_COLOR,
    GAME_OVER_HIGHLIGHT_COLOR,
)
from core.types.color import Color  # noqa: E402


# Win messages to preview (matching what each game mode would use)
WIN_MESSAGES = [
    ("Shrinking Mode", "Win: Fully Shrunk!"),
    ("AutoPlay", "Win: Board Complete!"),
    ("Box Mode", "Win: All Boxes Cleared!"),
    ("Classic (fill board)", "Win: Perfect Game!"),
    ("Default/Other", "Win:"),  # Tests the fallback message
    ("Game Over (loss)", "Hit wall"),  # Compare with regular game over
]


def main():
    pygame.init()

    width, height = 960, 800
    screen = pygame.display.set_mode((width, height))
    pygame.display.set_caption("Victory Screen Preview - Use LEFT/RIGHT arrows")

    current_index = 0
    clock = pygame.time.Clock()

    font_path = "assets/font/GetVoIP-Grotesque.ttf"
    try:
        big_font = pygame.font.Font(font_path, 80)
        medium_font = pygame.font.Font(font_path, 40)
        small_font = pygame.font.Font(font_path, 24)
    except Exception:
        big_font = pygame.font.Font(None, 80)
        medium_font = pygame.font.Font(None, 40)
        small_font = pygame.font.Font(None, 24)

    print("\n=== Victory Screen Preview ===")
    print("Press LEFT/RIGHT to cycle through win screens")
    print("Press ESC or Q to quit\n")
    print(f"Showing: {WIN_MESSAGES[current_index][0]}")

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_q):
                    running = False
                elif event.key == pygame.K_RIGHT:
                    current_index = (current_index + 1) % len(WIN_MESSAGES)
                    print(f"Showing: {WIN_MESSAGES[current_index][0]}")
                elif event.key == pygame.K_LEFT:
                    current_index = (current_index - 1) % len(WIN_MESSAGES)
                    print(f"Showing: {WIN_MESSAGES[current_index][0]}")

        mode_name, death_reason = WIN_MESSAGES[current_index]
        is_victory = death_reason.startswith("Win:")

        # Get victory message
        if is_victory and len(death_reason) > 5:
            victory_message = death_reason[5:].strip()
        else:
            victory_message = "You completed the game!"

        # Clear screen
        screen.fill(Color.from_hex(ARENA_PRIMARY_COLOR).to_tuple())

        # Choose colors based on win/loss
        if is_victory:
            title_color = VICTORY_TITLE_COLOR
            message_color = VICTORY_MESSAGE_COLOR
            highlight_color = VICTORY_HIGHLIGHT_COLOR
            high_score_color = VICTORY_HIGH_SCORE_COLOR
            title_text = "You Win!"
        else:
            title_color = GAME_OVER_MESSAGE_COLOR
            message_color = GAME_OVER_MESSAGE_COLOR
            highlight_color = GAME_OVER_HIGHLIGHT_COLOR
            high_score_color = (255, 69, 0)
            title_text = "Game Over"

        # Render title
        title_surface = big_font.render(title_text, True, title_color)
        title_rect = title_surface.get_rect(center=(width // 2, height // 4))
        screen.blit(title_surface, title_rect)

        # Render victory message (only for wins)
        y_offset = height // 2.5
        if is_victory:
            msg_surface = medium_font.render(victory_message, True, message_color)
            msg_rect = msg_surface.get_rect(center=(width // 2, y_offset))
            screen.blit(msg_surface, msg_rect)
            y_offset += 60

        # Render "NEW HIGH SCORE!"
        hs_surface = medium_font.render("* NEW HIGH SCORE! *", True, high_score_color)
        hs_rect = hs_surface.get_rect(center=(width // 2, y_offset))
        screen.blit(hs_surface, hs_rect)
        y_offset += 60

        # Render score
        score_surface = medium_font.render("Score: 100", True, highlight_color)
        score_rect = score_surface.get_rect(center=(width // 2, y_offset))
        screen.blit(score_surface, score_rect)

        # Draw mode label at bottom
        label = small_font.render(
            f"[LEFT/RIGHT] Mode: {mode_name}  |  death_reason='{death_reason}'",
            True,
            (100, 100, 100),
        )
        screen.blit(label, (20, height - 40))

        pygame.display.flip()
        clock.tick(30)

    pygame.quit()


if __name__ == "__main__":
    main()
