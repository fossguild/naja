.PHONY: all dev help clean

# Default target - run checks
all: pre-commit

# Set up development environment
dev:
	@echo "Setting up development environment..."
	uv sync --dev
	uv run pre-commit install
	@echo "✅ Development environment ready!"
	@echo "Run 'make' to run checks or 'make run' to play the game"

# Run the game
run:
	uv run naja

# Format code
format:
	uv run ruff check --fix .
	uv run black .
	uv run ruff format .

# Lint code
lint:
	uv run ruff check .
	uv run black --check .

# Run pre-commit on all files
pre-commit:
	uv run pre-commit run --all-files

# Clean up
clean:
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -delete
	rm -rf .ruff_cache/

# Show help
help:
	@echo "Available targets:"
	@echo "  make          - Run pre-commit (default)"
	@echo "  make dev      - Set up development environment"
	@echo "  make run      - Run the game"
	@echo "  make format   - Format code"
	@echo "  make lint     - Lint code"
	@echo "  make clean    - Clean up temporary files"
