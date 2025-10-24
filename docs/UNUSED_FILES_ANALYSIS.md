# Unused Code Analysis

## Files Moved to Tests

### 1. ✅ MOVED: `src/ecs/systems/ui/ui_system.py` → `tests/legacy/ui_system.py`
**Reason:** Only used in tests, never in actual game
**Status:** ✅ Moved in commit 3aff07e

---

## Deprecated Files Still in src/

### 2. 🔴 `src/ecs/systems/ui_system.py` (270 lines) - **DEPRECATED**
**Status:** Marked as DEPRECATED in docstring
**Imports:** None found in src/ or tests/
**Recommendation:** Move to `tests/legacy/` or delete entirely

**Evidence:**
```python
"""UISystem - handles all user interaction flows and menu navigation.

DEPRECATED: This file is legacy test code. The actual game uses scene-based
architecture (MenuScene, GameplayScene, etc.). Kept for backward compatibility
with existing tests.
"""
```

**Verification:**
```bash
$ grep -r "from src.ecs.systems.ui_system import" src/ tests/
# No results - file is not imported anywhere!
```

---

## Legacy Backup Files

### 3. 📦 `kobra_legacy.py` (589 lines)
**Purpose:** Backup of original kobra.py before refactoring
**Status:** Intentional archive for reference
**Recommendation:** Keep for documentation purposes, or move to `docs/archive/`

---

## Old Code Directory

### 4. 📁 `old_code/` 
**Contents:** Only `__pycache__/` (empty)
**Recommendation:** Delete entire directory

---

## Summary

| File | Lines | Status | Action |
|------|-------|--------|--------|
| `src/ecs/systems/ui/ui_system.py` | - | ✅ Moved | Already moved to tests/legacy/ |
| `src/ecs/systems/ui_system.py` | 270 | 🔴 Unused | **Move to tests/legacy/** |
| `kobra_legacy.py` | 589 | 📦 Archive | Keep or move to docs/ |
| `old_code/` | - | 📁 Empty | **Delete directory** |

---

## Active Code (KEEP)

All files in:
- `src/ecs/entities/` - Used by prefabs and systems
- `src/ecs/components/` - All components are used
- `src/ecs/systems/` (except ui_system.py) - All systems are active
- `src/game/scenes/` - All scenes are active
- `src/game/services/` - All services are active

