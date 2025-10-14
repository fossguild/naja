Copyright 2023 Monaco F. J. <monaco@usp.br>

Naja is free software and distributed under the terms of the GNU General
Public License 3.0.

Naja - Snake Game Programming Exercise
==============================

Naja (formerly KobraPy) is a programming exercise inspired by the classic 1980s snake game.

Implemented in Python, it provides a minimal yet functional codebase designed
for progressive extension by learners. Naja was originally conceived as an
instructional resource to introduce undergraduate computer science students to
open-source development practices and project management methodologies. Beyond
this initial purpose, the project can also serve as a complementary resource
within formal training programs or as a framework for independent study.

Naja is free software and may be redistributed under the terms of the GNU
General Public License version 3 or any later version.

The exercise involves:

a) Fixing known issues listed in the repository. b) Enhancing the game by adding
new and engaging features.

Quick Start
------------------------------

### For Players

**Requirements**: Python 3.12+ and [uv package manager](https://docs.astral.sh/uv/getting-started/installation/)
1. **Run the game** (dependencies are installed automatically):
   ```bash
   make run
   # Or directly: uv run python naja.py
   ```

### For Contributors

**Requirements**: Python 3.12+, [uv](https://docs.astral.sh/uv/getting-started/installation/)

1. **Set up development environment:**
   ```bash
   make dev
   # This runs: uv sync --dev && uv run pre-commit install
   ```

2. **Common development commands:**
   ```bash
   make run      # Play the game
   make          # Run code quality checks (linting, formatting)
   make format   # Format code with Black and Ruff
   make lint     # Check code quality
   make clean    # Remove temporary files
   ```

3. **Before contributing:**
   - Read `docs/CONTRIBUTING.md` for detailed guidelines
   - Create an issue first to discuss your changes
   - Follow the Git workflow described in the contributing guide

Getting Started
------------------------------

Detailed user instructions are available in `docs/manual.md`.

If you enjoy the project, the author would greatly appreciate hearing from you —
just send an e-mail.

Contributing
------------------------------

Contributions to Naja are most welcome. Please see `docs/CONTRIBUTING.md` for
directions on how to get started.
