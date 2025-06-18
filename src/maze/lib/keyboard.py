import os
import sys
import termios
import tty

from maze.lib.constants import Direction
from maze.lib.exceptions import InvalidKeyError


class CharGetter:
    def __init__(self, length: int) -> None:
        self.length = length
        self.stdin = sys.stdin.fileno()

    def read_chars(self) -> str:
        chars = ""
        while not chars:
            new_string = sys.stdin.read(1)
            if new_string == "\x03":
                sys.tracebacklimit = 0
                raise KeyboardInterrupt
            os.set_blocking(self.stdin, False)
            rest = sys.stdin.read(self.length + 10)
            os.set_blocking(self.stdin, True)
            chars = new_string + rest
        return chars

    def __call__(self) -> str:
        old_settings = termios.tcgetattr(self.stdin)
        tty.setraw(self.stdin)
        try:
            char = self.read_chars()
        finally:
            termios.tcsetattr(self.stdin, termios.TCSADRAIN, old_settings)
        return char


def get_direction() -> Direction:
    char_getter = CharGetter(3)
    match char_getter():
        case "\x1b[A":
            return Direction.UP
        case "\x1b[B":
            return Direction.DOWN
        case "\x1b[C":
            return Direction.RIGHT
        case "\x1b[D":
            return Direction.LEFT
        case _:
            return Direction(0)


def get_yes_no() -> bool:
    char_getter = CharGetter(1)
    match key := char_getter():
        case "y" | "Y" | "\r":
            return True
        case "n" | "N":
            return False
        case _:
            raise InvalidKeyError(key)


def clear() -> None:
    os.system("clear")  # noqa: S605, S607
