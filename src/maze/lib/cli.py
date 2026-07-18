from __future__ import annotations

import sys
from argparse import ArgumentParser, Namespace
from dataclasses import dataclass
from typing import Self

from maze.__version__ import __version__
from maze.lib.constants import DEFAULT_COLUMNS, DEFAULT_ROWS

sys.tracebacklimit = 0


@dataclass(frozen=True, slots=True)
class CliArgs:
    columns: int
    rows: int
    verbosity: int

    @classmethod
    def from_args(cls, args: Namespace, /) -> Self:
        return cls(
            columns=args.columns,
            rows=args.rows,
            verbosity=args.verbosity,
        )


def _positive_int(value: str) -> int:
    number = int(value)
    if number < 1:
        msg = "must be a positive integer"
        raise ValueError(msg)
    return number


def parse_args() -> CliArgs:
    parser = ArgumentParser(prog="maze", description="A simple maze game")
    parser.add_argument(
        "-V",
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
        help="print the version and exit",
    )
    parser.add_argument("-c", "--columns", type=_positive_int, default=DEFAULT_COLUMNS)
    parser.add_argument("-r", "--rows", type=_positive_int, default=DEFAULT_ROWS)
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        dest="verbosity",
        help="increase the level of verbosity",
    )

    args = parser.parse_args()
    if args.verbosity > 0:
        sys.tracebacklimit = 1000

    return CliArgs.from_args(args)
