# Naja - AI Assistant Guide

This document provides comprehensive information about the Naja project to help AI coding assistants understand the codebase, conventions, and best practices.

## Project Overview

**Naja** (originally KobraPy) is a classic snake game implemented in Python using Pygame. It serves as both a playable game and a programming exercise designed to teach open-source development practices and project management methodologies.

### Key Facts
- **Language**: Python 3.12+
- **Main Framework**: Pygame 2.6.1+
- **License**: GPL-3.0-or-later
- **Architecture**: Single-file application (`kobra.py`)
- **Repository**: https://github.com/fossguild/naja

## Project Structure

```
├── kobra.py              # Main game file (all game logic)
├── pyproject.toml        # Python project configuration
├── uv.lock              # UV lock file for dependencies
├── Makefile             # Build automation
├── README.md            # Project readme
├── AUTHORS              # Contributors list
├── COPYING              # License file
├── assets/
│   ├── font/            # Game fonts (GetVoIP Grotesque)
│   └── sound/           # Sound effects (gameover.wav)
└── docs/
    ├── CONTRIBUTING.md  # Contribution guidelines
    ├── conventions.md   # Project conventions
    ├── exercise.md      # Programming exercise instructions
    ├── issues.md        # Known bugs and feature requests
    └── manual.md        # User manual
```

## Code Architecture

### Main Components

The game is implemented in a single file (`kobra.py`) with the following structure:

1. **Game Configuration** (lines 24-103)
   - Display settings (grid size, window dimensions)
   - Color schemes (snake, apple, arena, UI)
   - Game parameters (speed, settings)
   - Menu field definitions

2. **Settings System** (lines 105-263)
   - `SETTINGS` dict: central configuration store
   - `MENU_FIELDS`: declarative menu configuration
   - `apply_settings()`: applies changes and resizes display
   - `run_settings_menu()`: modal settings UI loop

3. **UI Helpers** (lines 265-346)
   - `_draw_center_message()`: renders centered text with auto-sizing
   - `_wait_for_keys()`: blocking key input handler
   - `game_over_prompt()`: game over screen logic

4. **Menus** (lines 354-413)
   - `start_menu()`: main menu (Start Game / Settings)
   - Supports keyboard and mouse input

5. **Game Classes** (lines 420-540)
   - `Snake`: player-controlled snake with movement, collision detection, scoring
   - `Apple`: randomly spawned collectible with collision avoidance

6. **Drawing Functions** (lines 547-551)
   - `draw_grid()`: renders the game grid

7. **Main Game Loop** (lines 557-642)
   - Event handling (keyboard input, quit events)
   - Game state updates
   - Rendering (arena, grid, snake, apple, score)
   - Collision detection and apple collection

### Key Design Patterns

- **Pygame-based event loop**: Standard game loop with event polling
- **Object-oriented design**: Snake and Apple as classes
- **Declarative configuration**: `SETTINGS` and `MENU_FIELDS` for easy extension
- **Modal dialogs**: Settings and start menu block game execution
- **Dynamic resizing**: Game adjusts to screen size and user settings

## Development Guidelines

### Code Style

- **Formatter**: Black (configured in pyproject.toml)
- **Linter**: Ruff (configured in pyproject.toml)
- **Pre-commit hooks**: Automatically format and lint before commits
- **Language**: All code, comments, and documentation in English
- **Comments**: Use proper capitalization and punctuation
- **Naming**: Follow Python conventions (snake_case for functions/variables, PascalCase for classes)

### Development Workflow

1. **Branch Strategy**: GitFlow
   - `main`: stable releases
   - `dev`: active development
   - `feat/<issue>/<description>`: feature branches
   - `hot/<issue>/<description>`: hotfix branches
   - `wip/<issue>/<description>`: work-in-progress

2. **Commit Messages**: Use tag-based format
   ```
   tag: short imperative description

   Optional longer explanation with proper punctuation.
   ```
   Tags: `code`, `doc`, `build`, `repo`, `minor`, `other`

3. **Issue Tracking**: All changes must relate to a GitHub issue

### Setting Up Development Environment

```bash
# Install dependencies (requires uv)
uv sync --group dev

# Install pre-commit hooks
pre-commit install

# Run the game
./kobra.py  # Linux/MacOS
python kobra.py  # Windows
```

## Known Issues and TODOs

### Critical Bugs (from docs/issues.md)

1. **Self-bite detection bug**: When snake has only one tail segment, reversing direction doesn't detect self-collision
2. **Apple spawn collision**: Small chance apple spawns on snake, causing false self-bite detection

### Suggested Features

- Random snake starting position
- Enhanced settings menu with:
  - Username input
  - Difficulty levels (easy, normal, hard, nightmare, custom)
  - Multiple apples
  - Movement reversal toggle
  - Timed apples
  - Special apple types (poisoned, bounty)
  - Progressive difficulty
- High score persistence

## Game Mechanics

### Controls

- **Arrow keys / WASD**: Move snake (up, down, left, right)
- **Q**: Quit game
- **P**: Pause/unpause
- **M**: Open settings menu during gameplay
- **Mouse**: Click menu items

### Game Rules

- Snake continuously moves in current direction
- Eating apples increases score and snake length
- Touching borders or self = game over
- Speed increases progressively with each apple (up to MAX_SPEED)
- Score = number of tail segments

### Settings

- **Cells per side**: Grid dimensions (10-60)
- **Initial speed**: Starting game speed (1.0-40.0)
- **Max speed**: Speed cap (4.0-60.0)
- **Death sound**: Toggle game over sound effect

## Important Constants

```python
GRID_SIZE = 50              # Pixel size of each grid cell
WIDTH = HEIGHT              # Square game window
CLOCK_TICKS = 4            # Initial snake speed (updates/sec)
HEAD_COLOR = "#00aa00"      # Snake head color
TAIL_COLOR = "#00ff00"      # Snake body color
APPLE_COLOR = "#aa0000"     # Apple color
ARENA_COLOR = "#202020"     # Background color
```


### Changing Game Behavior

- **Speed mechanics**: Modify line 635 (`snake.speed = min(snake.speed * 1.1, MAX_SPEED)`)
- **Collision detection**: Snake.update() method (lines 452-516)
- **Scoring**: Main loop around line 627
- **Colors/appearance**: Constants at top of file (lines 46-53)

### Adding New Game Elements

1. Create a new class (similar to `Apple` or `Snake`)
2. Initialize in game setup (after line 559)
3. Update in main loop (around lines 611-637)
4. Draw in rendering section (lines 619-629)

## Testing and Quality Assurance

- **Manual testing**: Run game and test all features
- **Linting**: `ruff check .`
- **Formatting**: `black .`
- **Pre-commit**: Runs automatically on commit

## Licensing and Attribution

- **License**: GNU GPL v3 or later
- **Copyright**: Monaco F. J. <monaco@usp.br> (2023) and contributors
- **Derivative works**: Must maintain copyright notice and add your name
- **REUSE compliant**: Follow REUSE specification v3

## Quick Reference for AI Assistants

### When Making Changes

1. **Understand the context**: Read relevant sections of kobra.py
2. **Check existing patterns**: Follow established code style
3. **Test manually**: Game must run without errors
4. **Update documentation**: If adding features, update docs/manual.md
5. **Format code**: Run black and ruff before committing
6. **Preserve copyright**: Don't remove existing attribution

### Common Tasks

- **Bug fixes**: Focus on Snake.update() for collision detection
- **New features**: Extend SETTINGS and MENU_FIELDS for configuration
- **UI changes**: Modify menu rendering functions
- **Performance**: Optimize main loop or collision detection
- **Assets**: Add to assets/ directory and load in initialization

### Code Quality Checks

Do:
- Use descriptive variable names
- Add comments for complex logic
- Follow existing indentation and style
- Test all code paths
- Update documentation when changing behavior

Don't:
- Remove copyright notices
- Break existing functionality
- Use unclear variable names
- Skip pre-commit checks
- Add features without issue tracking
