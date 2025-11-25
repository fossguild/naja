from ecs.world import World
from ecs.board import Board
from ecs.prefabs.snake import create_snake
from ecs.prefabs.obstacle_field import create_obstacles, _get_safe_zone_cells


def test_obstacle_safe_zone_logic():
    """Test that _get_safe_zone_cells returns the correct cells."""
    board = Board(width=10, height=10, cell_size=1)
    world = World(board)

    # Create snake at (5, 5) moving right (dx=1, dy=0)
    snake_id = create_snake(world, grid_size=1)
    snake = world.registry.get(snake_id)
    snake.position.x = 5
    snake.position.y = 5
    snake.velocity.dx = 1
    snake.velocity.dy = 0

    safe_cells = _get_safe_zone_cells(world)
    expected_safe = {(6, 5), (7, 5), (8, 5)}

    assert expected_safe.issubset(safe_cells)


def test_obstacle_safe_zone_boundary_check():
    """Test that _get_safe_zone_cells respects board boundaries."""
    board = Board(width=10, height=10, cell_size=1)
    world = World(board)

    # Create snake at (9, 5) moving right (dx=1, dy=0)
    # This is at the edge, so safe zone would be (10, 5), (11, 5), (12, 5) which are out of bounds
    snake_id = create_snake(world, grid_size=1)
    snake = world.registry.get(snake_id)
    snake.position.x = 9
    snake.position.y = 5
    snake.velocity.dx = 1
    snake.velocity.dy = 0

    safe_cells = _get_safe_zone_cells(world)

    # Should be empty as all potential safe cells are out of bounds
    assert len(safe_cells) == 0


def test_create_obstacles_respects_safe_zone():
    """Test that create_obstacles does not spawn obstacles in the safe zone."""
    board = Board(width=10, height=10, cell_size=1)
    world = World(board)

    # Create snake at (5, 5) moving right (dx=1, dy=0)
    snake_id = create_snake(world, grid_size=1)
    snake = world.registry.get(snake_id)
    snake.position.x = 5
    snake.position.y = 5
    snake.velocity.dx = 1
    snake.velocity.dy = 0

    # Generate obstacles
    obstacle_ids = create_obstacles(
        world, "Impossible", False, grid_size=1, random_seed=42
    )

    obstacles = [world.registry.get(oid) for oid in obstacle_ids]

    safe_zone = {(6, 5), (7, 5), (8, 5)}

    for obs in obstacles:
        pos = (obs.position.x, obs.position.y)
        assert pos not in safe_zone, f"Obstacle spawned in safe zone at {pos}"
