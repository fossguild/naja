# Next Steps

## Visual Elements

- ### Fluidity

  Visual elements should be polished and have a sense of fluidity.

- ### Design

  The elements which will be designed include:
  - Snake
  - Apple
  - Arena
  - Board

  Some of these elements will need animations (multiple sprites) and multiple color palettes.

## Game Modes

Each game mode will be unique and separate from each other.

Some of the game modes which were discussed at the brain storm class were:

- Normal (Classic snake game)
- Random (Will select a random game mode each time)
- Mirrored (There are two snakes on the board, one is a mirror image of the other)
- Flying Apple (The apple moves around the board)
- Cheese (The snakes have holes in them which the player can use to their advantage)
- Flipping Head (When an apple is eaten, the snake's head switches to the tail)
- Obstacle Spawn (When 2 apples are eaten, a fixed obstacle spawns on the board)
- AutoPlay (The snake plays itself, the player just watches)
- Teleport (The snake can teleport to a random location on the board when an apple is eaten)

## Settings, Scoreboard and Persistence

It would be interesting to have a scoreboard that displays the top scores for each game mode.
The scoreboard should consider differences at settings, such as speed, board size and apple count.

Both the scoreboard and settings should be persistent, meaning they are saved between sessions. This can be achieved by saving the data classes as a json in the user local storage (in windows, this would be in the AppData folder, and in Linux in the ~/.local/share).
