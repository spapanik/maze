from __future__ import annotations

from unittest import mock

from maze.game.maze import Maze, Position, all_directions
from maze.lib.constants import Direction

FULLY_WALLED = {
    Position(0, 0): all_directions,
    Position(0, 1): all_directions,
    Position(1, 0): all_directions,
    Position(1, 1): all_directions,
}
# A single corridor: (0,0) → (0,1) → (1,1) → (1,0)
CLOCKWISE_CORRIDOR = {
    Position(0, 0): Direction.UP | Direction.DOWN | Direction.LEFT,
    Position(0, 1): Direction.UP | Direction.RIGHT,
    Position(1, 0): Direction.UP | Direction.DOWN | Direction.LEFT,
    Position(1, 1): Direction.DOWN | Direction.RIGHT,
}
# A single corridor: (0,0) → (1,0) → (1,1) → (0,1)
ANTICLOCKWISE_CORRIDOR = {
    Position(0, 0): Direction.UP | Direction.LEFT | Direction.RIGHT,
    Position(0, 1): Direction.UP | Direction.LEFT | Direction.RIGHT,
    Position(1, 0): Direction.DOWN | Direction.LEFT,
    Position(1, 1): Direction.DOWN | Direction.RIGHT,
}


def render(matrix: dict[Position, Direction]) -> str:
    maze = Maze(2, 2)
    maze.matrix = matrix
    return str(maze)


def test_str_renders_walls_between_all_cells() -> None:
    expected = "┌───┬───┐\n│ * │   │\n├───┼───┤\n│   │ X │\n└───┴───┘\n"
    assert render(FULLY_WALLED) == expected


def test_str_renders_a_clockwise_corridor() -> None:
    expected = "┌───────┐\n│ *     │\n├────   │\n│     X │\n└───────┘\n"
    assert render(CLOCKWISE_CORRIDOR) == expected


def test_str_renders_an_anticlockwise_corridor() -> None:
    expected = "┌───┬───┐\n│ * │   │\n│   │   │\n│     X │\n└───────┘\n"
    assert render(ANTICLOCKWISE_CORRIDOR) == expected


def test_move_respects_walls_and_open_passages() -> None:
    maze = Maze(3, 3)
    maze.matrix = {position: Direction(0) for position in maze.matrix}
    maze.matrix[Position(1, 1)] = Direction.UP
    maze.position = Position(1, 1)

    maze.move(Direction.UP)
    assert maze.position == Position(1, 1)

    maze.move(Direction.DOWN)
    assert maze.position == Position(2, 1)

    maze.move(Direction.UP)
    assert maze.position == Position(1, 1)

    maze.move(Direction.LEFT)
    assert maze.position == Position(1, 0)

    maze.move(Direction.RIGHT)
    assert maze.position == Position(1, 1)

    maze.move(Direction.UP | Direction.DOWN)
    assert maze.position == Position(1, 1)


def test_initialize_matrix_carves_left_then_backtracks_right() -> None:
    with (
        mock.patch("maze.game.maze.randbelow", side_effect=[0, 1]),
        mock.patch("maze.game.maze.choice", side_effect=lambda options: options[0]),
    ):
        maze = Maze(1, 3)

    assert maze.matrix == {
        Position(0, 0): Direction.UP | Direction.DOWN | Direction.LEFT,
        Position(0, 1): Direction.UP | Direction.DOWN,
        Position(0, 2): Direction.UP | Direction.DOWN | Direction.RIGHT,
    }


def test_initialize_matrix_carves_up_then_backtracks_down() -> None:
    with (
        mock.patch("maze.game.maze.randbelow", side_effect=[1, 0]),
        mock.patch("maze.game.maze.choice", side_effect=lambda options: options[0]),
    ):
        maze = Maze(3, 1)

    assert maze.matrix == {
        Position(0, 0): Direction.UP | Direction.LEFT | Direction.RIGHT,
        Position(1, 0): Direction.LEFT | Direction.RIGHT,
        Position(2, 0): Direction.DOWN | Direction.LEFT | Direction.RIGHT,
    }
