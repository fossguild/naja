#!/usr/bin/env python3
"""Test collision logic to verify wall collision boundary."""


def test_wall_collision():
    """Test wall collision at boundary."""
    grid_width = 19
    electric_walls = True

    test_cases = [
        # (current_x, dx, description)
        (17, 1, "Moving from 17 to 18 (should be OK)"),
        (18, 1, "Moving from 18 to 19 (should COLLIDE)"),
        (16, 1, "Moving from 16 to 17 (should be OK)"),
        (0, -1, "Moving from 0 to -1 (should COLLIDE)"),
        (1, -1, "Moving from 1 to 0 (should be OK)"),
    ]

    for current_x, dx, description in test_cases:
        # Calculate next position (same logic as _get_snake_next_position)
        next_x = current_x + dx

        # Check collision (same logic as _check_wall_collision)
        collision = electric_walls and (next_x < 0 or next_x >= grid_width)

        status = "COLLISION" if collision else "OK"
        print(f"{description}")
        print(f"  current_x={current_x}, dx={dx}, next_x={next_x}")
        print(f"  Result: {status}")
        print()


if __name__ == "__main__":
    print("Testing wall collision logic with grid_width=19")
    print("=" * 60)
    print()
    test_wall_collision()
