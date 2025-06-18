from unittest import mock

import pytest

from maze.lib.cli import parse_args


@pytest.mark.parametrize(
    ("verbosity", "expected"), [("-v", 1), ("-vv", 2), ("-vvvvv", 5)]
)
def test_maze_verbose(verbosity: str, expected: int) -> None:
    with mock.patch("sys.argv", ["maze", verbosity]):
        args = parse_args()

    assert args.verbosity == expected


def test_sudoku_solver_verbose() -> None:
    with mock.patch("sys.argv", ["solve", "-c", "12", "-r", "15"]):
        args = parse_args()

    assert args.columns == 12
    assert args.rows == 15


def test_sudoku_solver_defaults() -> None:
    with mock.patch("sys.argv", ["maze"]):
        args = parse_args()

    assert args.columns == 16
    assert args.rows == 9
