import sys
from argparse import ArgumentParser, Namespace

from maze.__version__ import __version__
from maze.lib.constants import DEFAULT_COLUMNS, DEFAULT_ROWS

sys.tracebacklimit = 0


def parse_args() -> Namespace:
    parser = ArgumentParser(description="A simple maze game")
    parser.add_argument(
        "-V",
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
        help="print the version and exit",
    )
    parser.add_argument("-c", "--columns", type=int, default=DEFAULT_COLUMNS)
    parser.add_argument("-r", "--rows", type=int, default=DEFAULT_ROWS)
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

    return args
