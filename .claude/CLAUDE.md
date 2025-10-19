# Naja - ECS Architecture Project

This project is migrating from a monolithic snake game to an Entity-Component-System (ECS) architecture.

## Key Documentation
- See `.cursor/rules/` for comprehensive ECS architecture guidelines
- Start with `ecs_overview.mdc` for high-level understanding
- Refer to `ecs_migration_plan.mdc` for implementation steps

## Architecture Summary
- **Entities**: Just IDs, no data or logic
- **Components**: Pure data classes, no methods
- **Systems**: All game logic, inheriting from GameSystem base class

## Important Rules
- Components are pure data (dataclasses)
- Systems contain all logic
- RenderSystem is read-only (never modifies game state)
- UISystem handles all user interactions, delegates rendering
- All systems inherit from GameSystem abstract base
- Comments always start lowercase
- Never use em dash character
- Use Black formatting and Ruff linting

