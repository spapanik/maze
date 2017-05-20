from unittest import mock

from maze.lib.parser import parse_args


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
