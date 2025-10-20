# ECS Migration Status

## Current Status: Step 3 (Phase 1 Complete) 

Following the migration plan from `.cursor/rules/ecs_migration_plan.mdc`

**Last Updated**: Step 3 - Phase 1 - Pygame IO Adapter created
**Branch**: `feat/202/create-pygame-io-adapter`

## Project Structure

```
naja/
├── src/
│   ├── core/                    [NEW] Core engine
│   │   ├── app.py               ⬜ Main game loop (skeleton)
│   │   ├── clock.py             ⬜ Fixed timestep (skeleton)
│   │   └── io/
│   │       └── pygame_adapter.py ✅ Pygame wrapper (IMPLEMENTED)
│   │
│   ├── ecs/                     [NEW] ECS framework
│   │   ├── world.py             ⬜ World registry
│   │   │
│   │   ├── components/          [NEW] 16 components
│   │   │   ├── position.py      ⬜
│   │   │   ├── velocity.py      ⬜
│   │   │   ├── snake_body.py    ⬜
│   │   │   ├── apple.py         ⬜
│   │   │   ├── obstacle.py      ⬜
│   │   │   ├── renderable.py    ⬜
│   │   │   ├── collider.py      ⬜
│   │   │   ├── score.py         ⬜
│   │   │   ├── grid.py          ⬜
│   │   │   ├── flags.py         ⬜
│   │   │   ├── difficulty.py    ⬜
│   │   │   ├── palette.py       ⬜
│   │   │   ├── interpolation.py ⬜
│   │   │   ├── audio_queue.py   ⬜
│   │   │   ├── music_state.py   ⬜
│   │   │   └── ui_state.py      ⬜
│   │   │
│   │   ├── systems/             [NEW] 13 systems
│   │   │   ├── input.py         ⬜
│   │   │   ├── movement.py      ⬜
│   │   │   ├── collision.py     ⬜
│   │   │   ├── spawn.py         ⬜
│   │   │   ├── scoring.py       ⬜
│   │   │   ├── audio.py         ⬜
│   │   │   ├── render.py        ⬜
│   │   │   ├── ui.py            ⬜
│   │   │   ├── interpolation.py ⬜
│   │   │   ├── settings_apply.py ⬜
│   │   │   ├── validation.py    ⬜
│   │   │   ├── obstacle_generation.py ⬜
│   │   │   └── resize.py        ⬜
│   │   │
│   │   └── prefabs/             [NEW] 3 prefabs
│   │       ├── snake.py         ⬜
│   │       ├── apple.py         ⬜
│   │       └── obstacle_field.py ⬜
│   │
│   └── game/                    [NEW] Game layer
│       ├── config.py            ⬜
│       ├── constants.py         ⬜
│       ├── settings.py          ⬜
│       │
│       ├── scenes/              [NEW] 3 scenes
│       │   ├── menu.py          ⬜
│       │   ├── gameplay.py      ⬜
│       │   └── game_over.py     ⬜
│       │
│       └── services/            [NEW] 2 services
│           ├── assets.py        ⬜
│           └── audio.py         ⬜
│
├── tests/                       [NEW] Test suite
│   ├── ecs/                     6 test files
│   └── game/                    3 test files
│
├── old_code/                    [MOVED] Old implementation
│   ├── entities.py              📦 Old classes
│   ├── state.py                 📦 Old GameState
│   ├── assets.py                📦 Old assets
│   ├── config.py                📦 Old config
│   ├── constants.py             📦 Old constants
│   └── settings.py              📦 Old settings
│
└── docs/
    ├── architecture.md          ⬜ ECS docs
    └── adr/
        └── 0001-choose-ecs.md   ⬜ Decision record
```

## Legend
- ✅ Fully implemented and tested
- 🔄 In progress (partial implementation)
- ⬜ Skeleton only (header, ready for implementation)
- 📦 Old code (preserved for reference)
- [NEW] Newly created directory
- [MOVED] Relocated old code

## Statistics

### Implementation Progress
- **Fully Implemented**: 1 file (pygame_adapter.py)
- **In Progress**: 0 files
- **Skeleton Only**: 56+ files
- **Old Code Preserved**: 6 files in `old_code/`

### Migration Steps
- **Total Steps**: 27
- **Completed**: 2 (Steps 1-2 structure)
- **In Progress**: 1 (Step 3 - Phase 1/9 complete)
- **Remaining**: 24
- **Overall Progress**: ~7.4%

## Migration Steps Progress

Based on `.cursor/rules/ecs_migration_plan.mdc`

### ✅ Step 1: Create ECS Infrastructure (COMPLETE)
**Goal**: Establish basic ECS framework without changing game behavior

**Completed Tasks**:
- ✅ Created `src/ecs/world.py` skeleton
- ✅ Created empty component dataclasses in `src/ecs/components/`
- ✅ Created abstract `GameSystem` base class skeleton
- ✅ Created empty system classes in `src/ecs/systems/`
- ⬜ Write unit tests for world registry (TODO)

**Status**: Structure complete, implementation pending

---

### ✅ Step 2: Migrate Core Loop (COMPLETE)
**Goal**: Move game loop to `src/core/app.py`

**Completed Tasks**:
- ✅ Created `src/core/app.py` skeleton
- ✅ Created `src/core/clock.py` skeleton
- ⬜ Update `kobra.py` to bootstrap app (TODO)
- ⬜ Move frame limiting and delta time calculation (TODO)

**Status**: Structure complete, implementation pending

---

### 🔄 Step 3: Create Pygame IO Adapter (IN PROGRESS)
**Goal**: Wrap pygame-specific code for testability

**Phase 1 - Create Adapter** ✅ COMPLETE:
- ✅ Created `src/core/io/pygame_adapter.py` with `PygameAdapter` class
- ✅ Implemented 12 static wrapper methods:
  - `init()`, `init_mixer()` (initialization)
  - `create_display()`, `set_caption()`, `update_display()` (display)
  - `poll_events()`, `wait_for_event()` (events)
  - `draw_rect()`, `create_surface()`, `create_rect()` (drawing)
  - `get_ticks()`, `create_clock()` (time)
- ✅ Re-exported 17 pygame constants (QUIT, KEYDOWN, K_* keys, etc.)
- ✅ Added comprehensive docstrings
- ✅ Game still runs identically (no changes to kobra.py yet)

**Phase 2-9 - Migrate Usage** ⬜ TODO:
- ⬜ Phase 2: Migrate initialization (pygame.init, mixer.init)
- ⬜ Phase 3: Migrate display updates (display.update)
- ⬜ Phase 4: Migrate event polling (event.get, event.wait)
- ⬜ Phase 5: Migrate drawing primitives (draw.rect)
- ⬜ Phase 6: Migrate surface creation (Surface)
- ⬜ Phase 7: Migrate screen/caption (set_mode, set_caption)
- ⬜ Phase 8: Migrate time functions (get_ticks)
- ⬜ Phase 9: Migrate clock (Clock)

**Acceptance Criteria**:
- ✅ Game renders identically
- ✅ Events processed same way
- ✅ No visual or behavioral changes

**Current Phase**: 1/9 complete

---

### ⬜ Step 4: Define All Components
**Goal**: Create all component dataclasses as pure data

**Tasks**:
- ⬜ Implement each component in `src/ecs/components/`
- ⬜ Add docstrings explaining purpose and usage
- ⬜ Add type hints for all fields
- ⬜ Keep components frozen where data doesn't change
- ⬜ Write unit tests for component creation

**Components to implement** (16 total):
- position.py, velocity.py, snake_body.py
- edible.py (apple), obstacle.py, renderable.py
- collider.py, score.py, grid.py
- flags.py, difficulty.py, palette.py
- interpolation.py, audio_queue.py, music_state.py, ui_state.py

---

### ⬜ Step 5: Implement GameSystem Base Class
**Goal**: Create abstract base with shared context

**Tasks**:
- ⬜ Implement `GameSystem` abstract class
- ⬜ Add constructor with dependency injection
- ⬜ Add lifecycle hooks (on_attach, on_detach, update, etc.)
- ⬜ Add property getters for shared context
- ⬜ Add guard helpers (require_running_pygame, require_not_paused)

---

### ⬜ Step 6-7: Migrate RenderSystem
**Goal**: Extract rendering logic into RenderSystem

**Part 1** (Step 6):
- ⬜ Create `RenderSystem` inheriting `GameSystem`
- ⬜ Move grid drawing logic
- ⬜ Move obstacle drawing logic
- ⬜ Move apple drawing logic

**Part 2** (Step 7):
- ⬜ Move snake drawing logic
- ⬜ Implement interpolation for smooth movement
- ⬜ Handle edge wrapping

---

### ⬜ Step 8-9: Migrate UISystem
**Goal**: Extract menu logic into UISystem

**Part 1** (Step 8):
- ⬜ Create `UISystem` inheriting `GameSystem`
- ⬜ Move start menu loop
- ⬜ Implement `run_start_menu()`

**Part 2** (Step 9):
- ⬜ Move settings menu loop
- ⬜ Move reset warning dialog
- ⬜ Move game over prompt

---

### ⬜ Step 10: Implement Command Protocol
- ⬜ Create command dataclasses (Move, Pause, Quit, etc.)
- ⬜ Implement `handle_in_game_event()` in UISystem
- ⬜ Update main loop to process commands

---

### ⬜ Step 11: Migrate Settings Application
- ⬜ Implement `apply_settings(reset_objects)` in UISystem
- ⬜ Move window resize logic
- ⬜ Move font reload logic
- ⬜ Move entity recreation logic

---

### ⬜ Step 12: Migrate InputSystem
- ⬜ Create `InputSystem` inheriting `GameSystem`
- ⬜ Move direction input handling
- ⬜ Move pause, quit, menu handling
- ⬜ Move music toggle and palette randomize

---

### ⬜ Step 13: Migrate MovementSystem
- ⬜ Create `MovementSystem` inheriting `GameSystem`
- ⬜ Extract snake movement logic
- ⬜ Implement grid wrapping
- ⬜ Handle body segment following

---

### ⬜ Step 14: Migrate CollisionSystem
- ⬜ Create `CollisionSystem` inheriting `GameSystem`
- ⬜ Extract apple collision detection
- ⬜ Extract wall collision detection
- ⬜ Extract obstacle and self-collision detection
- ⬜ Emit collision events

---

### ⬜ Step 15: Migrate SpawnSystem
- ⬜ Create `SpawnSystem` inheriting `GameSystem`
- ⬜ Extract apple spawning logic
- ⬜ Implement free cell detection
- ⬜ Handle spawn retry logic

---

### ⬜ Step 16: Migrate ObstacleGenerationSystem
- ⬜ Create `ObstacleGenerationSystem` inheriting `GameSystem`
- ⬜ Extract constructive generation
- ⬜ Extract connectivity check (flood fill)
- ⬜ Extract trap detection logic

---

### ⬜ Step 17: Migrate ScoringSystem
- ⬜ Create `ScoringSystem` inheriting `GameSystem`
- ⬜ Listen for ate_apple events
- ⬜ Update score component
- ⬜ Update high score component

---

### ⬜ Step 18: Migrate AudioSystem
- ⬜ Create `AudioSystem` inheriting `GameSystem`
- ⬜ Implement SFX queue processing
- ⬜ Implement music control
- ⬜ Handle multiple simultaneous SFX

---

### ⬜ Step 19: Migrate InterpolationSystem
- ⬜ Create `InterpolationSystem` inheriting `GameSystem`
- ⬜ Calculate interpolation alpha
- ⬜ Detect edge wrapping
- ⬜ Update Interpolation component

---

### ⬜ Step 20: Migrate ValidationSystem
- ⬜ Create `ValidationSystem` inheriting `GameSystem`
- ⬜ Verify exactly one apple exists
- ⬜ Verify snake position in bounds
- ⬜ Verify no invalid entity overlap

---

### ⬜ Step 21: Migrate ResizeSystem
- ⬜ Create `ResizeSystem` inheriting `GameSystem`
- ⬜ Detect window resize events
- ⬜ Recalculate cell size
- ⬜ Update grid component

---

### ⬜ Step 22: Create Prefabs
- ⬜ Implement `create_snake()` in `src/ecs/entities/snake.py`
- ⬜ Implement `create_apple()` in `src/ecs/entities/apple.py`
- ⬜ Implement `create_obstacles()` in `src/ecs/entities/obstacle_field.py`
- ⬜ Replace old class constructors with prefab calls

---

### ⬜ Step 23: Wire Systems in Gameplay Scene
- ⬜ Create `src/game/scenes/gameplay.py`
- ⬜ Register systems in execution order
- ⬜ Call lifecycle hooks (on_attach)
- ⬜ Update main loop to use scene

---

### ⬜ Step 24: Remove Old Code
- ⬜ Remove `old_code/entities.py`
- ⬜ Remove `old_code/state.py`
- ⬜ Remove old rendering code from `kobra.py`
- ⬜ Remove old input handling from `kobra.py`
- ⬜ Remove deprecation comments

---

### ⬜ Step 25: Add System Tests
- ⬜ Write unit tests for MovementSystem
- ⬜ Write unit tests for CollisionSystem
- ⬜ Write unit tests for SpawnSystem
- ⬜ Write unit tests for ScoringSystem
- ⬜ Write unit tests for InterpolationSystem
- ⬜ Write integration tests for full game flow

---

### ⬜ Step 26: Documentation Updates
- ⬜ Write `docs/architecture.md` explaining ECS
- ⬜ Write `docs/adr/0001-choose-ecs.md` with rationale
- ⬜ Update `docs/manual.md`
- ⬜ Update `docs/CONTRIBUTING.md` with ECS guidelines
- ⬜ Update README.md with architecture overview

---

### ⬜ Step 27: Final Verification
- ⬜ Manual testing: full game playthrough
- ⬜ Test all menus and settings
- ⬜ Test edge cases: wrapping, electric walls, obstacles
- ⬜ Screenshot comparison for visual regression
- ⬜ Performance testing: verify frame rate unchanged


---

## Notes

- Migration follows incremental approach (small commits, game always playable)
- Each step has clear acceptance criteria
- Old code preserved in `old_code/` for reference
- All new files have GPL-3.0 license headers
- Following `.cursor/rules/ecs_migration_plan.mdc` strictly

