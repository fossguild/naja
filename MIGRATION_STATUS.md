# ECS Migration Status

## Phase 0: Structure Setup ✓ COMPLETE

All blank files have been created following the ECS architecture.
Old functional code has been moved to `old_code/` directory.

## Project Structure

```
naja/
├── src/
│   ├── core/                    [NEW] Core engine
│   │   ├── app.py               ⬜ Main game loop
│   │   ├── clock.py             ⬜ Fixed timestep
│   │   └── io/
│   │       └── pygame_adapter.py ⬜ Pygame wrapper
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
- ⬜ Blank file (header only, ready for implementation)
- 📦 Old code (preserved for reference)
- [NEW] Newly created directory
- [MOVED] Relocated old code

## Statistics

### Files Created
- **Core**: 5 files
- **ECS Components**: 16 files
- **ECS Systems**: 13 files
- **ECS Prefabs**: 3 files
- **Game Layer**: 9 files
- **Tests**: 9 files
- **Documentation**: 2 files
- **Total**: 57+ files created

### Old Code Moved
- 6 files moved to `old_code/`

## Implementation Order (Recommended)

### Phase 1: Foundation
1. ✓ Create directory structure
2. ⬜ Implement World registry
3. ⬜ Create GameSystem abstract base class
4. ⬜ Implement basic components (Position, Velocity)

### Phase 2: Core Systems
5. ⬜ Implement MovementSystem
6. ⬜ Implement InputSystem
7. ⬜ Implement CollisionSystem
8. ⬜ Implement SpawnSystem

### Phase 3: Rendering
9. ⬜ Implement RenderSystem
10. ⬜ Implement InterpolationSystem
11. ⬜ Implement UISystem

### Phase 4: Game Logic
12. ⬜ Implement ScoringSystem
13. ⬜ Implement AudioSystem
14. ⬜ Implement remaining systems

### Phase 5: Integration
15. ⬜ Create prefab factories
16. ⬜ Wire scenes together
17. ⬜ Update kobra.py bootstrap

### Phase 6: Testing & Cleanup
18. ⬜ Write unit tests
19. ⬜ Write integration tests
20. ⬜ Remove old_code/

## Git Status

Current branch: `feat/196/update-ai-docs`

**Deleted from src/:**
- assets.py
- config.py
- constants.py
- entities.py
- settings.py
- state.py

**Untracked (new):**
- old_code/
- src/core/
- src/ecs/
- src/game/
- tests/
- docs/architecture.md
- docs/adr/

## Next Actions

1. Review the structure created
2. Start implementing World registry (core of ECS)
3. Follow the migration plan in `.cursor/rules/ecs_migration_plan.mdc`
4. Implement systems one by one with tests
5. Keep game functional throughout migration

## Notes

- All files have GPL-3.0 license headers ✓
- All files pass linting (ruff) ✓
- Structure matches documentation ✓
- Old code preserved for reference ✓
- Ready for implementation phase ✓
