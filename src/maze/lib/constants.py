from enum import Flag, auto
from pathlib import Path

CONFIG_PATH = Path.home().joinpath(".config", "maze", "config.toml")
DEFAULT_ROWS = 9
DEFAULT_COLUMNS = 16


class Direction(Flag):
    UP = auto()
    DOWN = auto()
    LEFT = auto()
    RIGHT = auto()
