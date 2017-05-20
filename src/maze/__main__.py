from maze.game.game import play
from maze.lib.parser import parse_args


def main() -> None:
    args = parse_args()
    play(args.rows, args.columns)
