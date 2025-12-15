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

"""Central definition of the available game modes."""

GameModeType = str

CLASSIC_MODE_NAME = "Classic Snake Game"
MOVING_APPLE_MODE_NAME = "Moving Apple"
HEAD_TAIL_SWITCH_NAME = "Head-Tail Swap"
CHEESE_MODE_NAME = "Cheese Mode"
AUTOPLAY_MODE_NAME = "AutoPlay"
SHRINKING_MODE_NAME = "Shrinking Mode"
TELEPORT_MODE_NAME = "Teleport"
BOX_MODE_NAME = "Box Mode"
TRAIL_MODE_NAME = "Trail Mode"
LIGHTS_OUT_MODE_NAME = "Lights Out"
PLAYER_VS_PLAYER_MODE_NAME = "Player vs Player"
MIRRORED_MODE_NAME = "Mirrored"

ACTUAL_GAME_MODES = [
    {
        "name": CLASSIC_MODE_NAME,
        "description": "Classic snake gameplay with stationary apples and default settings.",
        "detailed_info": "The original Snake experience! Control your snake to eat apples and grow longer. Apples stay in one place until you eat them. Avoid hitting walls or your own body. Each apple makes you grow and increases your score. Perfect for learning the basics!",
    },
    {
        "name": MOVING_APPLE_MODE_NAME,
        "description": "Apples drift slowly around the board, forcing constant pursuit.",
        "detailed_info": "Apples won't wait for you! In this challenging mode, apples slowly drift across the board in random directions. You need to chase them down before they move away. This adds a layer of difficulty as you can't just plan a simple path - you must adapt to the moving targets!",
    },
    {
        "name": HEAD_TAIL_SWITCH_NAME,
        "description": "State toggle when the snake consumes an apple.",
        "detailed_info": "Mind-bending mode where eating an apple swaps your head and tail positions! Your snake reverses direction instantly, turning your tail into the new head. This requires careful planning - what was safe behind you is now in front! Master spatial awareness to succeed.",
    },
    {
        "name": CHEESE_MODE_NAME,
        "description": "Snake body has holes - pass through them safely, but avoid solid segments!",
        "detailed_info": "Your snake's body has gaps like Swiss cheese! Some segments are solid (dangerous) while others are hollow (safe to pass through). You can move through the hollow segments without dying, opening up new strategic possibilities. Plan your routes carefully to use the holes to your advantage!",
    },
    {
        "name": SHRINKING_MODE_NAME,
        "description": "Snake starts large and shrinks as it eats apples until only the head remains.",
        "detailed_info": "Reverse growth mechanics! You start with a long snake and each apple you eat makes you SHORTER instead of longer. Your goal is to shrink down to just the head by eating all available apples. The challenge increases as you get smaller and have less room to maneuver!",
    },
    {
        "name": AUTOPLAY_MODE_NAME,
        "description": "The snake plays itself, the player just watches.",
        "detailed_info": "Sit back and watch! The snake uses AI to play itself automatically. No controls needed - just observe as the AI tries to survive and score points. Great for relaxing or studying AI pathfinding behavior. You can still access settings to customize the visual experience!",
    },
    {
        "name": TELEPORT_MODE_NAME,
        "description": "Collect an apple to warp to the other one, maintaining your direction.",
        "detailed_info": "Quantum snake mechanics! Two apples appear on the board. When you eat one, you instantly teleport to where the other apple was, maintaining your current direction. The eaten apple respawns at a new location. This creates unique strategic opportunities and escape routes!",
    },
    {
        "name": BOX_MODE_NAME,
        "description": "Push boxes into holes to earn points.",
        "detailed_info": "Sokoban meets Snake! Push boxes around the board into designated holes to score points. You can push boxes but not pull them, so plan your moves carefully to avoid getting stuck. Combines puzzle-solving with snake mechanics for a unique challenge!",
    },
    {
        "name": TRAIL_MODE_NAME,
        "description": "Every tile the snake moves through becomes a permanent obstacle.",
        "detailed_info": "Leave your mark - permanently! Every tile you move through becomes a solid obstacle that remains for the rest of the game. The board fills up as you play, creating an ever-shrinking maze. Requires careful path planning to avoid trapping yourself. How long can you survive?",
    },
    {
        "name": LIGHTS_OUT_MODE_NAME,
        "description": "Map completely black. Limited vision around the snake head.",
        "detailed_info": "The arena is completely dark. Each snake has a constant 4-tile vision radius around its head. Apples emit a 2-tile glow and are visible only when that glow intersects your vision. Choose your next move carefully!",
    },
    {
        "name": PLAYER_VS_PLAYER_MODE_NAME,
        "description": "Two players compete locally on the same board!",
        "detailed_info": "Grab a friend and compete head-to-head! Player 1 uses WASD, Player 2 uses Arrow keys. Each player has 3 lives and respawns after 3 seconds. Colliding with your opponent costs a life. Last player standing wins!",
    },
    {
        "name": MIRRORED_MODE_NAME,
        "description": "Two snakes move in opposite directions, mirrored across the board center.",
        "detailed_info": "Control two snakes simultaneously! They move in opposite directions, perfectly mirrored across the board center. When one snake eats food, both grow. If they collide with each other, you lose. Requires careful spatial planning!",
    },
]

RANDOM_MODE_LABEL = "Random"
RANDOM_MODE_INDEX = len(ACTUAL_GAME_MODES)

__all__ = [
    "CLASSIC_MODE_NAME",
    "MOVING_APPLE_MODE_NAME",
    "CHEESE_MODE_NAME",
    "AUTOPLAY_MODE_NAME",
    "TELEPORT_MODE_NAME",
    "BOX_MODE_NAME",
    "TRAIL_MODE_NAME",
    "LIGHTS_OUT_MODE_NAME",
    "PLAYER_VS_PLAYER_MODE_NAME",
    "MIRRORED_MODE_NAME",
    "ACTUAL_GAME_MODES",
    "RANDOM_MODE_LABEL",
    "RANDOM_MODE_INDEX",
]
