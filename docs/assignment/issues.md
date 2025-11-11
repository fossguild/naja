Known Issues
==============================

This is a list of issues you should consider in your project.

Known Bugs to Resolve (Required)
--------------------------------------

* ❌ **[UNRESOLVED]** In the current implementation, reversing movement (e.g., if the snake is
  moving right and the player presses the left key) is not treated as an
  illegal move. While this is intentional to add challenge (since it causes
  the snake to bite itself), there is a bug: the self-bite is not detected
  if the snake's tail has only one segment.

* ✅ **[RESOLVED]** There is a small random chance that an apple will be dropped onto the snake,
  and attempting to eat it is incorrectly detected as a self-bite. The
  probability is low, but it increases as the snake lengthens.
  
  **Status:** Fixed in `src/ecs/systems/apple_spawn.py:_get_occupied_positions()`.
  The method now properly checks both the snake head position and all body
  segments before spawning an apple, preventing apples from spawning on the snake.

Suggested Features to Consider (Optional)
------------------------------------------

* The snake should start at a random position (but not too close to the border
  it is initially heading toward).

* Initial Setup Menu

  Implement a startup menu where the user can configure the game.
  Possible options might include:

  - user name
  - grid size ✅
  - difficulty level: easy, normal, hard, nightmare, custom ✅

  These levels might affect:

  - snake speed ✅
  - number of apples in the arena ✅ 
  - whether reversing the snake'smovement is allowed
  - whether apples disappear after a certain time
  - whether poisoned apples appear that degrade energy
  - whether bounty apples appear that shorten the snake
  - whether the game progresses through phases of increasing difficulty

* Before the game starts, the user should be able to choose the level
  of difficulty. This might include preset parameter combinations, or dynamic
  difficulty scaling where the game becomes harder as the score increases.
  ✅ - Difficulty presets available

* The game should save the highest score. ✅
