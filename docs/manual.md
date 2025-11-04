NajaPy Manual
==============================

NajaPy is a programming exercise inspired by the classic 1980s snake game.

Implemented in Python, it provides a minimal yet functional codebase designed
for progressive extension by learners. NajaPy was originally conceived as an
instructional resource to introduce undergraduate computer science students to
open-source development practices and project management methodologies. Beyond
this original scope, the project may also serve as a complementary resource
within formal training programs or as a framework for independent study.

NajaPy is free software and may be distributed under the GNU General Public
License version 3 or any later version.

Requirements
------------------------------

* **Python 3.12+**
* **Pygame 2.6.1+** (https://www.pygame.org)
* **uv package manager** (https://docs.astral.sh/uv/getting-started/installation/)

## Development Requirements

If you want to contribute to the project, you'll also need:

* **pre-commit 3.0.0+**
* **black 24.0.0+**
* **ruff 0.6.0+**

These are automatically installed when you run `make dev`. Ruff and Black are the standard linter and formatter, and compliance is required before merging pull requests.

The Game
------------------------------

The game takes place in a rectangular arena where a snake continuously moves in
one of four orthogonal directions: left, right, up, or down; it never stops. The
challenge is to steer the snake using the keyboard to help it eat apples that
appear in random positions. Once consumed, apples disappear and respawn
elsewhere.

Be careful! The arena borders are electrified and will kill the snake if
touched. Moreover, the snake is poisonous to itself—it dies if its head crosses
its own tail.

The score is the number of apples eaten before the snake dies and the game ends.
The goal is to collect as many apples as possible.

But there’s a catch: the snake lengthens each time it eats an apple.

Controls
------------------------------

### Gameplay Controls
  * `arrow keys or WASD`: move the snake up, down, left, right
  * `Q`: quit to main menu
  * `P`: pause the game
  * `ESC or M`: open in-game settings (adjust audio and colors without exiting)
  * `N`: toggle audio (music and sound effects)
  * `C`: randomize snake colors

### In-Game Settings Menu
When you press `ESC` or `M` during gameplay, you can adjust:
  * Background Music (on/off)
  * Sound Effects (on/off)
  * Snake Color (choose from available palettes)
  * Return to Main Menu (quit current game)

Use `W/S` or arrow keys to navigate, `A/D` or arrow keys to adjust values, `Enter` to select, and `ESC` to return to the game.

Note: Settings that require a game reset (like grid size, speed, obstacles) are only available in the main menu before starting a game.

### Game Over
When the game ends, press any key to restart or 'q' to quit.

Getting Started
------------------------------

To get started with the project:

a) **Set up and try the game:**

   Run the game (dependencies are installed automatically): `make run`

b) **For development:**

   1. Set up development environment: `make dev`
   2. Run quality checks: `make`
   3. See all available commands: `make help`

c) **For the programming exercise:**

   Read the directions for the exercise in `docs/assignment/exercise.md`
