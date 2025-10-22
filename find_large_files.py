#!/usr/bin/env python3
"""
Script to find all Python files in the project with more than 350 lines.
"""

from pathlib import Path


def count_lines(file_path):
    """Count the number of lines in a file."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return len(f.readlines())
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return 0


def find_large_files(root_dir, min_lines=350, extensions=(".py",)):
    """
    Find all files with more than min_lines lines.

    Args:
        root_dir: Root directory to search
        min_lines: Minimum number of lines (default: 350)
        extensions: Tuple of file extensions to search (default: .py files)

    Returns:
        List of tuples (file_path, line_count) sorted by line count (descending)
    """
    large_files = []
    root_path = Path(root_dir)

    # Directories to skip
    skip_dirs = {
        "__pycache__",
        ".git",
        "venv",
        "env",
        ".venv",
        "node_modules",
        ".pytest_cache",
        "tests",
    }

    for file_path in root_path.rglob("*"):
        # Skip directories and files in skip_dirs
        if any(skip_dir in file_path.parts for skip_dir in skip_dirs):
            continue

        # Check if it's a file with the right extension
        if file_path.is_file() and file_path.suffix in extensions:
            line_count = count_lines(file_path)
            if line_count > min_lines:
                # Store relative path for cleaner output
                rel_path = file_path.relative_to(root_path)
                large_files.append((str(rel_path), line_count))

    # Sort by line count (descending)
    large_files.sort(key=lambda x: x[1], reverse=True)

    return large_files


def main():
    # Get the project root directory (where this script is located)
    project_root = Path(__file__).parent

    print(f"Searching for Python files with more than 350 lines in: {project_root}\n")
    print("=" * 80)

    large_files = find_large_files(project_root, min_lines=350)

    if large_files:
        print(f"\nFound {len(large_files)} file(s) with more than 350 lines:\n")
        print(f"{'File Path':<60} {'Lines':>10}")
        print("-" * 80)

        total_lines = 0
        for file_path, line_count in large_files:
            print(f"{file_path:<60} {line_count:>10}")
            total_lines += line_count

        print("-" * 80)
        print(f"{'TOTAL':>60} {total_lines:>10}")
        print(f"\nAverage lines per file: {total_lines // len(large_files)}")
    else:
        print("\nNo files found with more than 350 lines.")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
