# Naja ECS Architecture

> **Version:** 1.0  
> **Last Updated:** October 2025  
> **Status:** ✅ Fully Implemented

This document describes the Entity-Component-System (ECS) architecture used in the Naja snake game.

---

## Table of Contents

1. [Overview](#overview)
2. [What is ECS?](#what-is-ecs)
3. [Why ECS for Naja?](#why-ecs-for-naja)
4. [Core Principles](#core-principles)
5. [Architecture Components](#architecture-components)
6. [Game Flow](#game-flow)
7. [System Execution Order](#system-execution-order)
8. [Project Structure](#project-structure)
9. [Key Components](#key-components)
10. [Key Systems](#key-systems)
11. [Design Patterns](#design-patterns)
12. [Examples](#examples)
13. [Testing Strategy](#testing-strategy)
14. [References](#references)

---

## Overview

Naja is a classic snake game built using the **Entity-Component-System (ECS)** architectural pattern. ECS provides a clear separation between data (components), logic (systems), and entities, making the codebase:

- ✅ **Modular**: Each system has a single, well-defined responsibility
- ✅ **Testable**: Systems can be tested in isolation with mock components
- ✅ **Maintainable**: Small, focused systems are easier to understand and modify
- ✅ **Scalable**: New features can be added as new components and systems
- ✅ **Collaborative**: Multiple developers can work on different systems with minimal conflicts

---

## What is ECS?

ECS is an architectural pattern that separates game logic into three distinct concepts:

### **Entity**
- A unique identifier (just an integer)
- Serves as a container for components
- Has no logic or data itself
- Example: `entity_id = 42`

### **Component**
- Pure data structures (no methods, no logic)
- Describes one aspect of an entity
- Built using Python `@dataclass`
- Examples: `Position(x=10, y=20)`, `Velocity(dx=1, dy=0)`

### **System**
- Contains all game logic
- Processes entities that have specific component combinations
- Runs every game tick in a fixed order
- Examples: `MovementSystem`, `CollisionSystem`, `RenderSystem`

```
┌────────────────────────────────────────────────┐
│                   ENTITY 42                    │
│              (just an ID number)               │
└────────────────────────────────────────────────┘
                        │
        ┌───────────────┼───────────────┐
        │               │               │
        ▼               ▼               ▼
  ┌──────────┐   ┌──────────┐   ┌──────────┐
  │ Position │   │ Velocity │   │Renderable│
  │  x: 10   │   │ dx: 1    │   │color: red│
  │  y: 20   │   │ dy: 0    │   │shape:rect│
  └──────────┘   └──────────┘   └──────────┘
        │               │               │
        └───────────────┼───────────────┘
                        ▼
              ┌──────────────────┐
              │  MovementSystem  │
              │  RenderSystem    │
              └──────────────────┘
```

---

## Why ECS for Naja?

### **Benefits**

1. **Separation of Concerns**
   - Data (components) separated from logic (systems)
   - Easy to reason about what each part does

2. **Composition Over Inheritance**
   - Build complex entities by combining simple components
   - No deep inheritance hierarchies to navigate

3. **Testability**
   - Systems can be tested in isolation
   - Mock components are easy to create
   - No need for complex test fixtures

4. **Parallel Development**
   - Multiple developers can work on different systems simultaneously
   - Minimal merge conflicts since systems are independent

5. **Maintainability**
   - Small, focused systems (< 300 lines each)
   - Clear responsibilities and boundaries
   - Easy to find and fix bugs

### **Trade-offs**

1. **Initial Complexity**: More files and abstractions than a monolithic approach
2. **Learning Curve**: Team needs to understand ECS principles
3. **Indirection**: Following data flow requires understanding component-system relationships

For an educational project like Naja, these trade-offs are worthwhile as they teach valuable architectural patterns used in professional game development.

---

## Core Principles

### 1️⃣ **Components are Pure Data**

✅ **Good:**
```python
@dataclass
class Position:
    """Entity location in grid space."""
    x: float
    y: float
```

❌ **Bad:**
```python
@dataclass
class Position:
    x: float
    y: float
    
    def move(self, dx, dy):  # ❌ Logic in component!
        self.x += dx
        self.y += dy
```

### 2️⃣ **Systems Contain All Logic**

✅ **Good:**
```python
class MovementSystem(BaseSystem):
    def update(self, world: World) -> None:
        for entity_id in world.query(Position, Velocity):
            pos = world.get_component(entity_id, Position)
            vel = world.get_component(entity_id, Velocity)
            pos.x += vel.dx
            pos.y += vel.dy
```

❌ **Bad:**
```python
# Logic scattered across components
velocity.apply_to(position)  # ❌ Components calling each other!
```

### 3️⃣ **Entities are Just IDs**

✅ **Good:**
```python
snake_id = world.create_entity()
world.add_component(snake_id, Position(10, 20))
world.add_component(snake_id, Velocity(1, 0))
```

❌ **Bad:**
```python
class SnakeEntity:  # ❌ Entity with fields and methods!
    def __init__(self):
        self.x = 10
        self.y = 20
    def move(self):
        self.x += 1
```

### 4️⃣ **Systems are Independent**

✅ **Good:**
```python
# Systems communicate through components
class InputSystem:
    def update(self, world):
        # Read input, modify Velocity component
        
class MovementSystem:
    def update(self, world):
        # Read Velocity, modify Position component
```

❌ **Bad:**
```python
# Systems calling each other directly
movement_system.move_snake()  # ❌ Direct coupling!
```

---

## Architecture Components

### **World Registry**

Central hub that manages:
- Entity ID generation
- Component storage (maps `entity_id` → component instances)
- System registration and execution order
- Event queues for inter-system communication

**Location:** `src/ecs/world.py`

```python
world = World()
entity_id = world.create_entity()
world.add_component(entity_id, Position(10, 20))
position = world.get_component(entity_id, Position)
```

### **Prefabs**

Factory functions that create common entity configurations:

```python
def create_snake(world: World, start_x: int, start_y: int) -> int:
    """Create a snake entity with all necessary components."""
    entity_id = world.create_entity()
    world.add_component(entity_id, Position(start_x, start_y))
    world.add_component(entity_id, Velocity(1, 0))
    world.add_component(entity_id, SnakeBody(segments=[], length=3))
    world.add_component(entity_id, Collider(shape=SEGMENTS))
    world.add_component(entity_id, Renderable(color=(0, 255, 0)))
    return entity_id
```

**Location:** `src/ecs/prefabs/`

### **Scenes**

Scenes orchestrate systems for different game modes:

- **MenuScene**: Main menu, settings menu
- **GameplayScene**: Active gameplay with all game systems
- **GameOverScene**: Game over screen with restart option

Each scene registers systems in a specific order.

**Location:** `src/game/scenes/`

---

## Game Flow

Each game tick follows this execution order:

```
┌─────────────────────────────────────────────────────┐
│                   GAME TICK START                   │
└─────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────┐
│              1. INPUT PHASE                         │
│  InputSystem: Read events, update Velocity/GameState│
└─────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────┐
│              2. GAME LOGIC PHASE                    │
│  MovementSystem: Update positions                   │
│  CollisionSystem: Detect collisions, emit events    │
│  AppleSpawnSystem: Spawn apples as needed           │
│  ScoringSystem: Update score from events            │
│  ObstacleGenerationSystem: Generate obstacles       │
└─────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────┐
│              3. SETTINGS PHASE                      │
│  SettingsApplySystem: Apply runtime changes         │
│  ValidationSystem: Verify game state integrity      │
└─────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────┐
│              4. AUDIO PHASE                         │
│  AudioSystem: Play sounds and music                 │
└─────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────┐
│              5. RENDER PHASE                        │
│  InterpolationSystem: Calculate smooth positions    │
│  BoardRenderSystem: Draw grid and background        │
│  EntityRenderSystem: Draw game entities             │
│  SnakeRenderSystem: Draw snake with interpolation   │
│  UIRenderSystem: Draw HUD, score, overlays          │
└─────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────┐
│                  GAME TICK END                      │
│              Display update, repeat                 │
└─────────────────────────────────────────────────────┘
```

### **Pause Behavior**

When `GameState.paused = True`:
- Input system (0) **continues running** (to detect unpause)
- Game logic systems (1-8) **are skipped**
- Rendering systems (9+) **continue running** (frozen game with overlay)

---

## System Execution Order

Systems run in a **fixed order** each tick. This order is critical for correct behavior:

| # | System | Responsibility | Pausable? |
|---|--------|---------------|-----------|
| 0 | **InputSystem** | Read events, update Velocity/GameState | ❌ No |
| 1 | **MovementSystem** | Update positions based on velocity | ✅ Yes |
| 2 | **CollisionSystem** | Detect collisions, emit events | ✅ Yes |
| 3 | **AppleSpawnSystem** | Maintain correct apple count | ✅ Yes |
| 4 | **SpawnSystem** | Create new entities at valid positions | ✅ Yes |
| 5 | **ScoringSystem** | Update score from events | ✅ Yes |
| 6 | **ObstacleGenerationSystem** | Generate obstacles with connectivity | ✅ Yes |
| 7 | **SettingsApplySystem** | Apply runtime settings changes | ✅ Yes |
| 8 | **ValidationSystem** | Verify game state integrity | ✅ Yes |
| 9 | **InterpolationSystem** | Calculate smooth positions | ❌ No |
| 10 | **AudioSystem** | Play sounds and music | ❌ No |
| 11 | **BoardRenderSystem** | Draw grid and background | ❌ No |
| 12 | **EntityRenderSystem** | Draw game entities | ❌ No |
| 13 | **SnakeRenderSystem** | Draw snake with interpolation | ❌ No |
| 14 | **UIRenderSystem** | Draw HUD and overlays | ❌ No |

**Defined in:** `src/game/scenes/gameplay.py`

---

## Project Structure

```
naja/
├── kobra.py                    # Thin bootstrap entrypoint
├── pyproject.toml              # Project metadata, dependencies
├── Makefile                    # Common tasks (run, test, lint)
├── docs/
│   ├── architecture.md         # This file
│   ├── CONTRIBUTING.md         # Contribution guidelines
│   └── manual.md               # User documentation
│
├── src/
│   ├── core/                   # Core engine systems
│   │   ├── app.py              # Main game loop orchestrator
│   │   ├── clock.py            # Fixed timestep
│   │   └── io/
│   │       └── pygame_adapter.py  # Pygame I/O abstraction
│   │
│   ├── ecs/                    # ECS framework
│   │   ├── world.py            # Entity registry, component storage
│   │   ├── components/         # Pure data components (20+ files)
│   │   ├── systems/            # Logic systems (15+ files)
│   │   └── prefabs/            # Entity factories
│   │
│   └── game/                   # Game-specific code
│       ├── scenes/             # Scene managers (menu, gameplay, etc.)
│       ├── services/           # Singleton services (assets, audio)
│       ├── config.py           # Screen detection, dimensions
│       ├── constants.py        # Colors, defaults, magic numbers
│       └── settings.py         # Runtime configurable options
│
└── tests/                      # Test suite
    ├── ecs/                    # ECS unit tests
    ├── game/                   # Game integration tests
    └── legacy/                 # Deprecated test code
```

---

## Key Components

### **Position Component**
```python
@dataclass
class Position:
    """Entity location in grid or screen space."""
    x: float
    y: float
```
**Used by:** Snake, Apple, Obstacle, Wall

### **Velocity Component**
```python
@dataclass
class Velocity:
    """Movement direction and speed."""
    dx: int  # Direction: -1, 0, or 1
    dy: int  # Direction: -1, 0, or 1
```
**Used by:** Snake

### **SnakeBody Component**
```python
@dataclass
class Body:
    """Snake segments and growth queue."""
    segments: list[tuple[int, int]]
    length: int
    growth_queue: int = 0
```
**Used by:** Snake

### **GameState Component**
```python
@dataclass
class GameState:
    """Global game state flags."""
    paused: bool = False
    game_over: bool = False
    death_reason: str = ""
    next_scene: Optional[str] = None
```
**Used by:** Global game entity (singleton)

### **Score Component**
```python
@dataclass
class Score:
    """Current score and high score."""
    current: int = 0
    high_score: int = 0
```
**Used by:** Global game entity (singleton)

### **Renderable Component**
```python
@dataclass
class Renderable:
    """Visual representation data."""
    color: tuple[int, int, int]
    shape: str  # "rect", "circle", "sprite"
    layer: int  # Draw order
    visible: bool = True
```
**Used by:** Snake, Apple, Obstacle, Wall, HUD

**Full catalog:** See `src/ecs/components/` directory

---

## Key Systems

### **InputSystem** 
**File:** `src/ecs/systems/input.py`  
**Responsibility:** Convert raw pygame events into component mutations

**Reads:** Pygame events  
**Writes:** `Velocity`, `GameState`  
**Queries:** Entities with `Velocity` component

**Key behaviors:**
- Maps arrow keys/WASD to direction changes
- Prevents 180-degree turns
- Handles P (pause), Q (quit), M (menu), N (music toggle), C (palette randomize)
- Updates `GameState.paused` when P is pressed
- Sets `GameState.next_scene` when M is pressed

---

### **MovementSystem**
**File:** `src/ecs/systems/movement.py`  
**Responsibility:** Update entity positions based on velocity

**Reads:** `Position`, `Velocity`, `GameSettings`  
**Writes:** `Position`, `Body.segments`  
**Queries:** Entities with `Position` and `Velocity`

**Key behaviors:**
- Moves snake head by `(dx, dy)` each tick
- Updates snake body segments (follow the leader)
- Handles grid wrapping for non-electric walls
- Maintains snake segment history for rendering

---

### **CollisionSystem**
**File:** `src/ecs/systems/collision.py`  
**Responsibility:** Detect collisions and update game state

**Reads:** `Position`, `Body`, `GameSettings`  
**Writes:** `GameState`, `Score`, `Body.growth_queue`  
**Queries:** Entities with `Position` and collision tags

**Key behaviors:**
- Checks snake head against apples → increases score and snake length
- Checks snake head against walls (electric mode) → game over
- Checks snake head against obstacles → game over
- Checks snake head against its own body → game over
- Plays collision sounds via `AudioService`

---

### **RenderSystem (BoardRenderSystem, EntityRenderSystem, SnakeRenderSystem, UIRenderSystem)**
**Files:** `src/ecs/systems/*_render.py`  
**Responsibility:** Draw all visual elements to screen

**Reads:** `Position`, `Renderable`, `Body`, `GameSettings`, `Interpolation`  
**Writes:** None (read-only)  
**Queries:** Entities with `Position` and `Renderable`

**Key behaviors:**
- Clears screen with arena color
- Draws grid lines
- Draws obstacles as rectangles
- Draws snake with smooth interpolation
- Draws apples
- Draws UI overlays (score, music indicator, pause screen)

---

### **AudioSystem**
**File:** `src/ecs/systems/audio.py`  
**Responsibility:** Play sound effects and background music

**Reads:** `AudioState`, music state entity  
**Writes:** None (triggers pygame mixer)  
**Queries:** Entities with audio components

**Key behaviors:**
- Processes SFX queue, plays sounds on available channels
- Manages background music playback, pause, stop
- Respects music enabled flag

---

**Full catalog:** See `.cursor/rules/ecs_systems.mdc`

---

## Design Patterns

### **Singleton Components**

Some components exist on a single global entity:
- `GameState` - global game state flags
- `Score` - current and high score
- `GameSettings` - color scheme, difficulty, etc.

```python
# Get the global game state
game_state = world.get_singleton(GameState)
game_state.paused = True
```

### **Tag Components**

Components with no data, used to mark entity types:
- `ObstacleTag` - marks obstacles
- `EdibleTag` - marks apples

```python
@dataclass
class ObstacleTag:
    """Marker for obstacle entities."""
    pass
```

### **Event-Based Communication**

Systems communicate through:
1. **Component mutations:** One system writes, another reads
2. **Audio events:** Systems queue sounds via `AudioService`
3. **Scene transitions:** Systems set `GameState.next_scene`

### **Command Pattern**

Input events are converted to commands:
```python
@dataclass
class MoveCommand:
    """Command to change snake direction."""
    dx: int
    dy: int
```

### **Prefab Factories**

Common entity configurations are encapsulated:
```python
def create_snake(world: World, x: int, y: int) -> int:
    """Create a snake entity with all components."""
    entity_id = world.create_entity()
    world.add_component(entity_id, Position(x, y))
    world.add_component(entity_id, Velocity(1, 0))
    world.add_component(entity_id, Body(segments=[], length=3))
    world.add_component(entity_id, Renderable(color=(0, 255, 0)))
    return entity_id
```

---

## Examples

### **Example 1: Adding a New Component**

**Goal:** Add a `Speed` component to control entity movement speed.

```python
# 1. Create component file: src/ecs/components/speed.py
from dataclasses import dataclass

@dataclass
class Speed:
    """Movement speed multiplier."""
    value: float = 1.0
```

```python
# 2. Add to prefab: src/ecs/prefabs/snake.py
def create_snake(world, x, y):
    entity_id = world.create_entity()
    world.add_component(entity_id, Position(x, y))
    world.add_component(entity_id, Velocity(1, 0))
    world.add_component(entity_id, Speed(1.0))  # ← New component
    # ...
    return entity_id
```

```python
# 3. Use in system: src/ecs/systems/movement.py
def update(self, world):
    for entity_id in world.query(Position, Velocity, Speed):
        pos = world.get_component(entity_id, Position)
        vel = world.get_component(entity_id, Velocity)
        speed = world.get_component(entity_id, Speed)  # ← Read new component
        
        pos.x += vel.dx * speed.value  # ← Use speed multiplier
        pos.y += vel.dy * speed.value
```

### **Example 2: Adding a New System**

**Goal:** Add a `PowerupSystem` that spawns power-ups periodically.

```python
# 1. Create system file: src/ecs/systems/powerup.py
from src.ecs.systems.base_system import BaseSystem
from src.ecs.world import World

class PowerupSystem(BaseSystem):
    """Spawns power-ups at random positions."""
    
    def __init__(self, spawn_interval_ms: int):
        self._spawn_interval = spawn_interval_ms
        self._time_since_spawn = 0
    
    def update(self, world: World) -> None:
        """Update powerup spawning logic."""
        self._time_since_spawn += world.dt_ms
        
        if self._time_since_spawn >= self._spawn_interval:
            self._spawn_powerup(world)
            self._time_since_spawn = 0
    
    def _spawn_powerup(self, world: World) -> None:
        """Create a powerup entity at random position."""
        # Implementation here
        pass
```

```python
# 2. Register in scene: src/game/scenes/gameplay.py
def on_attach(self):
    self._systems.extend([
        InputSystem(...),
        MovementSystem(...),
        CollisionSystem(...),
        PowerupSystem(5000),  # ← New system: spawn every 5 seconds
        # ...
    ])
```

### **Example 3: Querying Entities**

```python
# Get all entities with Position and Velocity
for entity_id in world.query(Position, Velocity):
    pos = world.get_component(entity_id, Position)
    vel = world.get_component(entity_id, Velocity)
    print(f"Entity {entity_id} at ({pos.x}, {pos.y}) moving ({vel.dx}, {vel.dy})")

# Get the snake entity (assuming only one exists)
snake_entities = world.query(Position, Body)
if snake_entities:
    snake_id = list(snake_entities)[0]
    snake_pos = world.get_component(snake_id, Position)
```

---

## Testing Strategy

### **Unit Tests for Systems**

Test systems in isolation with mock components:

```python
def test_movement_system():
    # Arrange: Create world and entities
    world = World()
    entity_id = world.create_entity()
    world.add_component(entity_id, Position(10, 20))
    world.add_component(entity_id, Velocity(1, 0))
    
    # Act: Run system
    system = MovementSystem()
    system.update(world)
    
    # Assert: Check position changed
    pos = world.get_component(entity_id, Position)
    assert pos.x == 11
    assert pos.y == 20
```

### **Integration Tests**

Test full game scenarios:

```python
def test_snake_eats_apple():
    # Arrange: Create game with snake and apple
    world = create_test_world()
    snake_id = create_snake(world, 10, 20)
    apple_id = create_apple(world, 11, 20)  # Apple in front of snake
    
    # Act: Run game tick
    movement_system.update(world)
    collision_system.update(world)
    
    # Assert: Snake grew, apple removed, score increased
    body = world.get_component(snake_id, Body)
    assert body.growth_queue == 1
    assert not world.entity_exists(apple_id)
    
    score = world.get_singleton(Score)
    assert score.current > 0
```

**Test location:** `tests/ecs/` and `tests/game/`

---

## References

### **External Resources**

- [Entity-Component-System FAQ](https://github.com/SanderMertens/ecs-faq) - Comprehensive ECS guide
- [Game Programming Patterns: Component](https://gameprogrammingpatterns.com/component.html) - Classic book chapter
- [Pygame Documentation](https://www.pygame.org/docs/) - Pygame library reference

### **Project Documentation**

- `.cursor/rules/ecs_overview.mdc` - ECS architecture overview
- `.cursor/rules/ecs_entities_components.mdc` - Component catalog
- `.cursor/rules/ecs_systems.mdc` - System catalog
- `.cursor/rules/ecs_coding_standards.mdc` - Code style guide
- `.cursor/rules/ecs_testing.mdc` - Testing strategies
- `docs/CONTRIBUTING.md` - Contribution workflow
- `docs/manual.md` - User documentation

### **Architecture Decision Records**

- `docs/adr/0001-choose-ecs.md` - Why we chose ECS architecture

---

## Summary

Naja's ECS architecture provides a **clean separation of concerns** through:

1. **Pure data components** - No logic, just data structures
2. **Independent systems** - Single responsibility, no direct coupling
3. **Central world registry** - Entity and component management
4. **Fixed execution order** - Predictable, deterministic behavior
5. **Scene-based organization** - Different game modes with different system configurations

This architecture makes the codebase **maintainable**, **testable**, and **extensible**, providing an excellent foundation for learning game development and open-source collaboration.

---

**For more details, see:**
- Component catalog: `.cursor/rules/ecs_entities_components.mdc`
- System catalog: `.cursor/rules/ecs_systems.mdc`
- Code standards: `.cursor/rules/ecs_coding_standards.mdc`
- Project structure: `.cursor/rules/ecs_project_structure.mdc`
