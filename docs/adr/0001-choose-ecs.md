# ADR 0001: Choose ECS Architecture

## Status
Accepted

## Context
Naja is an educational open-source snake game built with Python and Pygame. The project needed an architecture that:
- Facilitates collaboration among multiple contributors
- Makes the codebase easy to understand and extend
- Separates concerns clearly (data vs logic)
- Enables thorough testing of game mechanics

Traditional object-oriented approaches (e.g., Snake class with all logic) tend to create large, coupled classes that are hard to test and modify collaboratively.

## Decision
Adopt the **Entity-Component-System (ECS)** architecture pattern:
- **Entities**: Game objects (Snake, Apple, Obstacle)
- **Components**: Pure data containers (`@dataclass`)
- **Systems**: All game logic, processing entities with specific components

This pattern separates data from behavior, making each piece small, focused, and testable.

## Consequences

**Positive:**
- ✅ Modularity: Each system does one thing (movement, collision, rendering, etc.)
- ✅ Testability: Systems can be tested in isolation
- ✅ Maintainability: Small files, clear responsibilities
- ✅ Collaboration: Less merge conflicts, easier code reviews
- ✅ Educational: Clear separation of concerns teaches good practices

**Negative:**
- ❌ More files/abstractions than traditional OOP
- ❌ Learning curve for contributors

**Mitigations:**
- Comprehensive documentation in `docs/architecture.md`
- Real examples using `AppleSpawnSystem` as reference
- Clear contribution pipeline for new features
