from enum import Flag, auto
from functools import partial
from pathlib import Path

from dj_settings import get_setting

project_dir = Path(__file__).parents[3]
maze_setting = partial(get_setting, project_dir=project_dir, filename="maze.yaml")

DEFAULT_ROWS: int = maze_setting("rows", sections=["app", "defaults"], default=9)
DEFAULT_COLUMNS: int = maze_setting("columns", sections=["app", "defaults"], default=16)


class Direction(Flag):
    UP = auto()
    DOWN = auto()
    LEFT = auto()
    RIGHT = auto()
