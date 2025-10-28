# Naja ECS Architecture

> **Version:** 2.0 (Simplified)
> **Last Updated:** October 2025
> **Status:** ✅ Fully Implemented

Essential guide to Naja's ECS architecture for contributors.

## Table of Contents

1. [What is ECS](#1-what-is-ecs)
2. [Why ECS](#2-why-ecs)
3. [Fundamental Principles](#3-fundamental-principles)
4. [Main Components](#4-main-components)
5. [Main Systems](#5-main-systems)
6. [Execution Order](#6-execution-order)
7. [How to Add Features](#7-how-to-add-features)
8. [Code Examples](#8-code-examples)
9. [Tests](#9-tests)





## 1. What is ECS?

**Entity-Component-System** is an architectural pattern that separates data from behavior:

* **Entity:** Game object (Snake, Apple, Obstacle)
* **Component:** Pure data without logic (`@dataclass`)
* **System:** All game logic, processes entities

```python
# Entity: Snake
snake = Snake(
    position=Position(x=10, y=20),      # where it is
    velocity=Velocity(dx=1, dy=0),      # where it's going
    body=SnakeBody(segments=[...]),     # body
    renderable=Renderable(...)          # how to draw
)

# Systems process these components:
# MovementSystem: reads velocity, updates position
# CollisionSystem: reads position, detects collisions
# RenderSystem: reads position + renderable, draws
```

## 2. Why ECS?

**Advantages:**
- ✅ **Modular:** each system does one thing
- ✅ **Testable:** isolated systems, easy to test
- ✅ **Maintainable:** small and focused code
- ✅ **Collaborative:** fewer merge conflicts

**Disadvantages:**
- ❌ More files/abstractions
- ❌ Learning curve

For an educational open-source project, the advantages outweigh the disadvantages.

## 3. Fundamental Principles

### Components = Pure Data

```python
@dataclass
class Position:
    """Position on the grid (in cell coordinates)."""
    x: int
    y: int
    prev_x: int = 0  # for interpolation
    prev_y: int = 0
```

### Systems = All Logic

```python
class MovementSystem(BaseSystem):
    """Moves entities based on velocity."""
    
    def update(self, world):
        # Query entities with position + velocity
        entities = world.registry.query_by_component("position", "velocity")
        
        for entity in entities.values():
            # Update position based on velocity
            entity.position.prev_x = entity.position.x
            entity.position.prev_y = entity.position.y
            entity.position.x += entity.velocity.dx
            entity.position.y += entity.velocity.dy
```

### Systems Communicate via Components

Systems **do not** call other systems. They modify components that other systems read:

```python
# ✅ Correct: InputSystem modifies velocity
velocity.dx = 1
velocity.dy = 0

# MovementSystem reads velocity and moves
position.x += velocity.dx

# ❌ Wrong: system calling another system
movement_system.move(entity)
```

## 4. Main Components

Components are `@dataclass` in `src/ecs/components/`:

### Spatial

```python
@dataclass
class Position:
    """Location on the grid."""
    x: int
    y: int
    prev_x: int = 0
    prev_y: int = 0

@dataclass
class Velocity:
    """Direction and speed."""
    dx: int  # -1, 0, or 1
    dy: int
    speed: float = 10.0  # cells per second
```

### Snake

```python
@dataclass
class SnakeBody:
    """Snake segments."""
    segments: list[Position]
    size: int = 1
    alive: bool = True
```

### Global State (Singleton)

```python
@dataclass
class GameState:
    """Global game state (one instance)."""
    paused: bool = False
    game_over: bool = False
    death_reason: str = ""
    next_scene: Optional[str] = None

@dataclass
class Score:
    """Score (one instance)."""
    current: int = 0
    high_score: int = 0
```

### Rendering

```python
@dataclass
class Renderable:
    """How to draw the entity."""
    shape: Literal["circle", "square", "rectangle", "text"]
    color: Color
    size: int = 20
    secondary_color: Optional[Color] = None  # tail color
    visible: bool = True
```

**See all:** `src/ecs/components/`

## 5. Main Systems

Systems in `src/ecs/systems/` process entities:

### Input

```python
class InputSystem(BaseSystem):
    """Converts input into component changes."""
    
    # Reads: pygame events
    # Writes: Velocity, GameState
    
    # Example: right arrow
    if key == K_RIGHT and velocity.dx != -1:
        velocity.dx = 1
        velocity.dy = 0
```

### Logic

```python
class MovementSystem(BaseSystem):
    """Moves entities based on velocity."""
    # Reads: Position, Velocity
    # Writes: Position

class CollisionSystem(BaseSystem):
    """Detects collisions."""
    # Reads: Position, SnakeBody
    # Writes: GameState, Score

class ScoringSystem(BaseSystem):
    """Updates score."""
    # Reads: Score, collision events
    # Writes: Score
```

### Rendering

```python
class SnakeRenderSystem(BaseSystem):
    """Draws the snake with interpolation."""
    # Reads: Position, SnakeBody, Renderable, Interpolation
    # Writes: pygame surface

class UIRenderSystem(BaseSystem):
    """Draws HUD, score, pause."""
    # Reads: Score, GameState
    # Writes: pygame surface
```

**See all:** `src/ecs/systems/`

## 6. Execution Order

Systems execute in **fixed order** each frame. This order is defined in `GameplayScene` and ensures that data flows correctly between systems.

### Concept: Three Execution Phases

Every game frame goes through **3 phases** in order:

#### **Phase 1: Input**
- **Goal:** Capture player actions
- **Behavior:** Always executed (even when paused)
- **Why?** The player needs to unpause the game
- **Example:** Read pressed keys and update snake direction

#### **Phase 2: Game Logic**
- **Goal:** Process rules and simulate the world
- **Behavior:** Pausable (doesn't execute when `GameState.paused = True`)
- **Why?** The game "freezes" when paused
- **Examples:**
  - Move entities based on velocity
  - Detect collisions
  - Spawn new objects
  - Update score
  - Generate obstacles
  - Apply settings

#### **Phase 3: Rendering & Audio**
- **Goal:** Present the game state to the player
- **Behavior:** Always executed (even when paused)
- **Why?** The player needs to see "PAUSED" on screen
- **Examples:**
  - Calculate smooth animations (interpolation)
  - Play sounds and music
  - Draw board
  - Draw entities
  - Draw UI (score, pause, etc)

### How Pause Works

```
When GameState.paused = True:

✅ PHASE 1 (Input)       → EXECUTES (to detect "unpause")
❌ PHASE 2 (Logic)       → SKIPS (game frozen)
✅ PHASE 3 (Rendering)   → EXECUTES (shows paused frame)
```

The implementation checks each system's index and skips those belonging to the logic phase when the game is paused.

### Why Order Matters

The execution order **within each phase** is critical to avoid bugs:

**✅ Correct Order:**
```
1. Read player input
2. Update velocity based on input
3. Move entities based on velocity
4. Detect collisions at new positions
5. Draw entities at final positions
```

**❌ Wrong Order causes problems:**
```
If rendering before moving:
→ Draws snake at old position (delayed movement)

If detecting collision before moving:
→ Detects collisions at old position (collision bugs)

If reading input after moving:
→ Input has 1 frame delay (sluggish controls)
```

### Rules for Adding Systems

When adding a new system, ask:

**1. Which phase does it belong to?**
- Input? → First position (always active)
- Game logic? → Middle (pausable)
- Rendering? → End (always active)

**2. What data does it read?**
- Place **after** systems that write that data

**3. What data does it write?**
- Place **before** systems that read that data

**Practical example:**
```
New PowerupSystem that:
- Reads: Position (written by MovementSystem)
- Writes: Speed (read by MovementSystem in next frame)

Correct order:
MovementSystem → PowerupSystem → CollisionSystem
```

### Where to See Current Order

The exact system order is in:
- **File:** `src/game/scenes/gameplay.py`
- **Method:** `GameplayScene.on_attach()` or `_create_systems()`

The system list is defined in that method and executed in order in `GameplayScene.update()`.

## 7. How to Add Features

This section shows the **complete pipeline** to add a feature to Naja, from idea to tested and integrated code.

### Contribution Pipeline

We'll use a **real example** already implemented in the project: **`AppleSpawnSystem`**

This system always maintains the correct number of apples in the game, spawning new ones when needed.

#### **Step 1: Plan the Feature**

Before starting to code, answer:

1. **What new components do I need?**
   - `AppleConfig` - configuration for how many apples should exist
   - Reuse: `Position`, `Renderable`, `Edible` (already exist)

2. **What new systems do I need?**
   - `AppleSpawnSystem` - maintains correct number of apples in game
   - Don't need to modify `CollisionSystem` (already removes eaten apples)

3. **What data does each system read/write?**
   ```
   AppleSpawnSystem:
   - Reads: AppleConfig (how many apples we want)
   - Reads: Apple entities (how many exist now)
   - Reads: Positions of Snake, Obstacles, other Apples
   - Writes: Creates new Apple entities via prefab
   ```

4. **Where in execution order?**
   ```
   AppleSpawnSystem → Phase 2 (Logic) - pausable
   Position: after CollisionSystem (which removes apples)
   Before ScoringSystem (to spawn before counting)
   ```

#### **Step 2: Create the Components**

**Required components:**
- `AppleConfig` - configuration for how many apples we want (new)
- `Position`, `Renderable`, `Edible` - reused (already existed)

```python
# src/ecs/components/apple_config.py
@dataclass
class AppleConfig:
    """Global apple configuration in the game."""
    desired_count: int = 1  # How many apples should exist
```

**Key concept:** Components are just data. `AppleConfig` is a singleton that stores **configuration**, not logic.

📁 **See full implementation:** [`src/ecs/components/apple_config.py`](../src/ecs/components/apple_config.py)

#### **Step 3: Create the Prefab**

**What it does:** Factory that creates apples with all necessary components.

```python
# src/ecs/prefabs/apple.py
def create_apple(world: World, x: int, y: int, grid_size: int, 
                 color=None, points=10, growth=1) -> int:
    """Creates apple at position (x, y) with configured components."""
    apple = Apple(
        position=Position(x=x, y=y),
        edible=Edible(points=points, growth=growth),
        renderable=Renderable(shape="circle", color=..., size=grid_size)
    )
    return world.registry.add(apple)
```

**Key concept:** Prefabs encapsulate entity creation. Makes it easy to reuse and maintain consistency.

📁 **See full implementation:** [`src/ecs/prefabs/apple.py`](../src/ecs/prefabs/apple.py)

#### **Step 4: Create the System**

**System responsibilities:**
1. Count how many apples exist
2. Compare with desired count
3. Spawn new ones if necessary
4. Find valid positions (avoid snake, obstacles, etc)

```python
# src/ecs/systems/apple_spawn.py
class AppleSpawnSystem(BaseSystem):
    def update(self, world: World) -> None:
        # 1. How many do we want?
        desired_count = self._get_desired_apple_count(world)
        
        # 2. How many do we have?
        current_apples = world.registry.query_by_type(EntityType.APPLE)
        current_count = len(current_apples)
        
        # 3. Spawn difference
        for _ in range(desired_count - current_count):
            position = self._find_valid_position(world)
            if position:
                create_apple(world, x=position[0], y=position[1], ...)
    
    def _find_valid_position(self, world):
        """Finds position that doesn't collide with anything."""
        occupied = self._get_occupied_positions(world)
        # Try to find free position...
```

**Key concepts:**
- System **only has logic**, no own data
- Uses **queries** to get data from components
- Uses **prefabs** to create entities
- Private methods organize responsibilities

📁 **See full implementation:** [`src/ecs/systems/apple_spawn.py`](../src/ecs/systems/apple_spawn.py)

#### **Step 5: Register the System**

**Where:** `src/game/scenes/gameplay.py` in the `on_attach()` method

```python
self._systems.extend([
    InputSystem(...),          # 0: Input (always active)
    MovementSystem(...),       # 1: Movement
    CollisionSystem(...),      # 2: Collision (removes eaten apples)
    AppleSpawnSystem(1000),    # 3: Spawn (restocks apples) ← HERE!
    ScoringSystem(...),        # 4: Scoring
    # ...
])
```

**Key concept:** Order matters! `AppleSpawnSystem` comes **after** `CollisionSystem` because:
- `CollisionSystem` removes eaten apples
- `AppleSpawnSystem` counts how many remain and spawns new ones
- If reversed, it would spawn before removing!

📁 **See where it's registered:** [`src/game/scenes/gameplay.py`](../src/game/scenes/gameplay.py)

#### **Step 6: Create the Tests**

**Create file:**
```bash
touch tests/ecs/test_apple_spawn.py
```

**Important tests:**

```python
# tests/ecs/test_apple_spawn.py

def test_spawn_maintains_apple_count():
    """System maintains desired number of apples."""
    # Setup: want 3 apples
    config = Entity(apple_config=AppleConfig(desired_count=3))
    world.registry.add(config)
    
    # Execute system
    system.update(world)
    
    # Verify: has 3 apples?
    assert len(world.registry.query_by_type(EntityType.APPLE)) == 3

def test_respawn_after_eating():
    """Spawns new apple when one is eaten."""
    # ... create apple, remove (simulate eating), execute system
    # ... verify new one spawned

def test_no_spawn_on_full_board():
    """Doesn't spawn if there's no space."""
    # ... fill entire board, try to spawn
    # ... verify didn't spawn

def test_avoids_snake_position():
    """Apple doesn't spawn on snake."""
    # ... create snake, spawn apple
    # ... verify it's not in same position
```

**Key concepts:**
- Test **setup** (create world, entities)
- Test **execution** (run system)
- Test **verification** (assert)
- Each test covers **one scenario**

📁 **See full tests:** [`tests/ecs/test_spawn_system.py`](../tests/ecs/test_spawn_system.py) (real project tests)

**Run:**
```bash
pytest tests/ecs/test_apple_spawn.py -v
pytest tests/ecs/  # all ECS tests
```

#### **Step 7: Integrate and Document**

**To contribute your feature:**

📚 **Follow the complete contribution guide:** [`docs/CONTRIBUTING.md`](CONTRIBUTING.md)

The guide covers:
- How to make atomic commits
- Commit message conventions
- How to create Pull Requests
- Code review process
- Documentation best practices

### Contribution Checklist

When adding a feature, verify:

- [ ] **Components created** with `@dataclass` and exported
- [ ] **Prefabs created** to facilitate entity creation
- [ ] **Systems implement `BaseSystem`** and `update(world)` method
- [ ] **Pausable systems check `GameState.paused`**
- [ ] **Systems registered in correct order** in `GameplayScene`
- [ ] **Unit tests** for each system
- [ ] **Integration tests** for complete flow
- [ ] **Documentation updated** (if necessary)
- [ ] **Code follows conventions** of the project (see `CONTRIBUTING.md`)

## 8. Code Examples

### Entity Queries

```python
# Query by components - returns dict[int, Entity]
entities = world.registry.query_by_component("position", "velocity")
for entity_id, entity in entities.items():
    print(f"Entity {entity_id} at ({entity.position.x}, {entity.position.y})")

# Query by type - returns dict[int, Entity]
from src.ecs.entities.entity import EntityType
snakes = world.registry.query_by_type(EntityType.SNAKE)
if snakes:
    entity_id, snake = next(iter(snakes.items()))
    print(f"Snake at ({snake.position.x}, {snake.position.y})")

# Combined query (type + components)
snakes = world.registry.query_by_type_and_components(
    EntityType.SNAKE, "position", "velocity", "body"
)
```

### Access Singleton Component

```python
# GameState is singleton (one instance)
def _get_game_state(world):
    entities = world.registry.query_by_component("game_state")
    if entities:
        entity = next(iter(entities.values()))
        return getattr(entity, "game_state", None)
    return None

# Usage:
game_state = _get_game_state(world)
if game_state:
    if game_state.paused:
        return  # Skip system
    game_state.game_over = True
```

### Create Entity with Prefab

```python
# Using prefab (recommended)
from src.ecs.prefabs.snake import create_snake

snake_id = create_snake(
    world,
    grid_size=20,
    initial_speed=10.0,
    head_color=(255, 0, 0),    # red
    tail_color=(255, 100, 100)  # light red
)

# Access created entity
snake = world.registry.get(snake_id)
snake.velocity.dx = 1
```

### System that Detects Collision

```python
class CollisionSystem(BaseSystem):
    """Detects snake vs apple/obstacle/wall collisions."""
    
    def update(self, world):
        # Get snake
        snakes = world.registry.query_by_type(EntityType.SNAKE)
        if not snakes:
            return
        
        snake_id, snake = next(iter(snakes.items()))
        head_pos = (snake.position.x, snake.position.y)
        
        # Check collision with apples
        apples = world.registry.query_by_type(EntityType.APPLE)
        for apple_id, apple in apples.items():
            apple_pos = (apple.position.x, apple.position.y)
            if head_pos == apple_pos:
                # Collision! Grow snake and remove apple
                snake.body.size += 1
                world.registry.remove(apple_id)
                
                # Update score
                score_entities = world.registry.query_by_component("score")
                if score_entities:
                    score_entity = next(iter(score_entities.values()))
                    score_entity.score.current += 10
```

## 9. Tests

### Test System

```python
# tests/ecs/test_movement_system.py
def test_movement_system_moves_entity():
    """MovementSystem should move entity based on velocity."""
    # Setup
    board = Board(width=20, height=20, cell_size=20)
    world = World(board)
    
    # Create test entity
    entity = Entity(
        position=Position(x=10, y=10),
        velocity=Velocity(dx=1, dy=0, speed=10.0)
    )
    entity_id = world.registry.add(entity)
    
    # Create system
    system = MovementSystem()
    
    # Simulate enough time to move
    world.dt_ms = 100  # 100ms
    
    # Execute
    system.update(world)
    
    # Verify
    entity = world.registry.get(entity_id)
    assert entity.position.x == 11
    assert entity.position.y == 10
```

### Test Integration

```python
def test_snake_eats_apple():
    """Snake should grow and score increase when eating apple."""
    # Setup
    board = Board(width=20, height=20, cell_size=20)
    world = World(board)
    
    # Create snake and apple at same position
    snake_id = create_snake(world, grid_size=20)
    snake = world.registry.get(snake_id)
    snake.position.x = 10
    snake.position.y = 10
    
    apple_id = create_apple(world, grid_size=20)
    apple = world.registry.get(apple_id)
    apple.position.x = 10
    apple.position.y = 10
    
    # Create score
    score_entity = Entity(score=Score(current=0))
    world.registry.add(score_entity)
    
    # Execute collision system
    collision_system = CollisionSystem(settings=None, audio_service=None)
    collision_system.update(world)
    
    # Verify
    assert snake.body.size == 2  # grew
    assert world.registry.get(apple_id) is None  # apple removed
    
    score_entities = world.registry.query_by_component("score")
    score_entity = next(iter(score_entities.values()))
    assert score_entity.score.current == 10
```

**Run tests:**
```bash
pytest                 # all tests
pytest tests/ecs/      # only ECS tests
pytest tests/ecs/test_movement_system.py  # specific test
```

---

## Summary

**Naja uses ECS to:**
- ✅ Separate data (components) from logic (systems)
- ✅ Keep code modular and testable
- ✅ Facilitate open-source contributions

**To contribute:**
1. Read components in `src/ecs/components/`
2. Read systems in `src/ecs/systems/`
3. See execution order in `src/game/scenes/gameplay.py`
4. Follow examples above to add features
5. Write tests in `tests/ecs/`

**Additional documentation:**
- `docs/CONTRIBUTING.md` - contribution guide
- `docs/manual.md` - user manual
- `.cursor/rules/` - detailed ECS rules

