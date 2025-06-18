from contextlib import suppress

from pyutilkit.term import SGRString
from pyutilkit.timing import Stopwatch

from maze.game.maze import Maze
from maze.lib.keyboard import clear, get_direction, get_yes_no


def game(rows: int, columns: int) -> None:
    maze = Maze(rows, columns)
    while not maze.player_escaped():
        clear()
        SGRString(maze).print()
        maze.move(get_direction())
    clear()
    SGRString(maze).print()


def new_game() -> bool:
    while True:
        SGRString("Do you want to play another game [Y/n]?\n> ").print(end="")
        with suppress(ValueError):
            return get_yes_no()
        SGRString("\x1b[1F\x1b[A")


def results(stopwatch: Stopwatch) -> None:
    clear()
    if (laps := len(stopwatch.laps)) == 1:
        SGRString(f"You played 1 game that took {stopwatch.laps[-1]}.").print()
        SGRString("Goodbye!").print()
        return
    average = stopwatch.average
    SGRString(
        f"You played {laps} games that took an average time of {average}."
    ).print()
    SGRString("Goodbye!").print()


def play(rows: int, columns: int) -> None:
    stopwatch = Stopwatch()
    while True:
        with stopwatch:
            game(rows, columns)
        SGRString(
            f"Congratulations! You escaped the maze in {stopwatch.laps[-1]}."
        ).print()
        if not new_game():
            results(stopwatch)
            return
