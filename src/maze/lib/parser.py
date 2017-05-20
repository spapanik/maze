import tomllib
from argparse import ArgumentParser, Namespace

from maze.lib.constants import CONFIG_PATH, DEFAULT_COLUMNS, DEFAULT_ROWS


def parse_config() -> tuple[int, int]:
    if not CONFIG_PATH.exists():
        return DEFAULT_ROWS, DEFAULT_COLUMNS
    with CONFIG_PATH.open("rb") as file:
        config = tomllib.load(file)
    defaults = config.get("defaults", {})
    rows = defaults.get("rows", DEFAULT_ROWS)
    columns = defaults.get("columns", DEFAULT_COLUMNS)
    return rows, columns


def parse_args() -> Namespace:
    default_rows, default_columns = parse_config()
    parser = ArgumentParser(prog="maze", description="A simple maze game")
    parser.add_argument("-r", "--rows", type=int, default=default_rows)
    parser.add_argument("-c", "--columns", type=int, default=default_columns)
    return parser.parse_args()
