KobraPy Manual
==============================

KobraPy is a programming exercise inspired by the classic 1980s snake game.

Implemented in Python, it provides a minimal yet functional codebase designed
for progressive extension by learners. KobraPy was originally conceived as an
instructional resource to introduce undergraduate computer science students to
open-source development practices and project management methodologies. Beyond
this original scope, the project may also serve as a complementary resource
within formal training programs or as a framework for independent study.

KobraPy is free software and may be distributed under the GNU General Public
License version 3 or any later version.

Requirements
------------------------------

* Python 3
* Pygame engine (https://www.pygame.org)

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

  * `arrow keys`: move the snake up, down, left, right
  * `Q / q`: quit the game at any time

When the game ends, press any key to restart or 'q' to quit.

Programming Exercise
------------------------------

To get started with the project:

a) Try the game yourself

   * Linux/MacOS: `./kobra.py`
   * Windows: `python kobra.py`

b) Read the directions for the exercise in `docs/exercise.md`