from __future__ import annotations

import curses
import locale
import sys
from contextlib import suppress
from dataclasses import dataclass, field
from time import monotonic
from typing import TYPE_CHECKING

from maze.game.maze import Maze
from maze.lib.constants import Direction

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable


REFRESH_INTERVAL_MS = 100
MIN_MAZE_SIZE = 1
MIN_BANNER_DIMENSION = 3
ESCAPE_KEY = 27

KEY_DIRECTIONS = {
    curses.KEY_UP: Direction.UP,
    curses.KEY_DOWN: Direction.DOWN,
    curses.KEY_LEFT: Direction.LEFT,
    curses.KEY_RIGHT: Direction.RIGHT,
}

WALL_CHARACTERS = {
    "─": "ACS_HLINE",
    "│": "ACS_VLINE",
    "┌": "ACS_ULCORNER",
    "┐": "ACS_URCORNER",
    "└": "ACS_LLCORNER",
    "┘": "ACS_LRCORNER",
    "├": "ACS_LTEE",
    "┤": "ACS_RTEE",
    "┬": "ACS_TTEE",
    "┴": "ACS_BTEE",
    "┼": "ACS_PLUS",
}
FALLBACK_WALL_CHARACTERS = {
    "─": "-",
    "│": "|",
    "┌": "+",
    "┐": "+",
    "└": "+",
    "┘": "+",
    "├": "+",
    "┤": "+",
    "┬": "+",
    "┴": "+",
    "┼": "+",
}


@dataclass
class GameTimer:
    """A monotonic timer that does not count time spent paused."""

    clock: Callable[[], float] = monotonic
    _started_at: float = field(init=False)
    _paused_at: float | None = field(init=False, default=None)
    _paused_duration: float = field(init=False, default=0.0)
    _stopped_at: float | None = field(init=False, default=None)

    def __post_init__(self) -> None:
        self._started_at = self.clock()

    @property
    def paused(self) -> bool:
        return self._paused_at is not None

    @property
    def running(self) -> bool:
        return self._stopped_at is None

    @property
    def elapsed(self) -> float:
        if self._stopped_at is not None:
            effective_now = self._stopped_at
        elif self._paused_at is not None:
            effective_now = self._paused_at
        else:
            effective_now = self.clock()
        return max(0.0, effective_now - self._started_at - self._paused_duration)

    def pause(self) -> None:
        if self.running and not self.paused:
            self._paused_at = self.clock()

    def resume(self) -> None:
        if self.running and self._paused_at is not None:
            self._paused_duration += self.clock() - self._paused_at
            self._paused_at = None

    def stop(self) -> float:
        if self._stopped_at is None:
            if self._paused_at is not None:
                self._stopped_at = self._paused_at
            else:
                self._stopped_at = self.clock()
        return self.elapsed


@dataclass
class GameSession:
    rows: int
    columns: int
    clock: Callable[[], float] = monotonic
    completed_times: list[float] = field(default_factory=list)
    maze: Maze = field(init=False)
    timer: GameTimer = field(init=False)
    escaped: bool = field(init=False, default=False)

    def __post_init__(self) -> None:
        self.restart(self.rows, self.columns)

    @property
    def average(self) -> float | None:
        if not self.completed_times:
            return None
        return sum(self.completed_times) / len(self.completed_times)

    @property
    def best(self) -> float | None:
        if not self.completed_times:
            return None
        return min(self.completed_times)

    def restart(self, rows: int | None = None, columns: int | None = None) -> None:
        self.rows = rows if rows is not None else self.rows
        self.columns = columns if columns is not None else self.columns
        self.maze = Maze(self.rows, self.columns)
        self.timer = GameTimer(self.clock)
        self.escaped = False
        self.check_for_escape()

    def check_for_escape(self) -> None:
        if not self.escaped and self.maze.player_escaped():
            self.escaped = True
            self.completed_times.append(self.timer.stop())


def format_duration(seconds: float) -> str:
    total_tenths = max(0, int(seconds * 10))
    hours, remainder = divmod(total_tenths, 36_000)
    minutes, remainder = divmod(remainder, 600)
    whole_seconds, tenths = divmod(remainder, 10)
    if hours:
        return f"{hours:d}:{minutes:02d}:{whole_seconds:02d}.{tenths}"
    return f"{minutes:02d}:{whole_seconds:02d}.{tenths}"


def _safe_addnstr(
    window: curses.window,
    row: int,
    column: int,
    text: str,
    width: int,
    attribute: int = 0,
) -> None:
    if width <= 0:
        return
    with suppress(curses.error):
        window.addnstr(row, column, text, width, attribute)


def _draw_top_bar(stdscr: curses.window, session: GameSession) -> None:
    _screen_rows, screen_columns = stdscr.getmaxyx()
    if session.timer.paused:
        state = "PAUSED"
        controls = "S:Size R:Restart P:Resume Q:Quit"
    elif session.escaped:
        state = "DONE"
        controls = "S:Size R:Restart Q:Quit"
    else:
        state = "PLAY"
        controls = "S:Size R:Restart P:Pause Q:Quit"
    statistics = [
        format_duration(session.timer.elapsed),
        f"#{len(session.completed_times)}",
    ]
    if session.best is not None and session.average is not None:
        statistics.extend(
            (
                f"Best {format_duration(session.best)}",
                f"Avg {format_duration(session.average)}",
            )
        )
    bar = (
        f" Maze {session.rows}x{session.columns} {state} | {controls} | "
        f"{' '.join(statistics)} "
    )
    _safe_addnstr(
        stdscr,
        0,
        0,
        bar.ljust(screen_columns),
        screen_columns,
        curses.A_REVERSE,
    )


def _draw_banner(stdscr: curses.window, message: str) -> None:
    screen_rows, screen_columns = stdscr.getmaxyx()
    if screen_rows < MIN_BANNER_DIMENSION or screen_columns < MIN_BANNER_DIMENSION:
        return
    banner = f" {message} "
    column = max(0, (screen_columns - len(banner)) // 2)
    _safe_addnstr(
        stdscr,
        screen_rows // 2,
        column,
        banner,
        max(0, screen_columns - column),
        curses.A_REVERSE | curses.A_BOLD,
    )


def _blank_maze_rows(maze_rows: list[str]) -> list[str]:
    """Build an empty frame with the same dimensions as the rendered maze."""
    width = max(map(len, maze_rows))
    return [
        f"┌{'─' * (width - 2)}┐",
        *[f"│{' ' * (width - 2)}│"] * (len(maze_rows) - 2),
        f"└{'─' * (width - 2)}┘",
    ]


def draw(stdscr: curses.window, session: GameSession) -> bool:
    """Draw the current game, returning whether it fits in the terminal."""
    stdscr.erase()
    screen_rows, screen_columns = stdscr.getmaxyx()
    maze_rows = str(session.maze).splitlines()
    if session.timer.paused:
        # Hide the maze while paused so the layout cannot be studied
        # while the timer is not counting.
        maze_rows = _blank_maze_rows(maze_rows)
    required_rows = len(maze_rows) + 2
    required_columns = max(map(len, maze_rows))

    _draw_top_bar(stdscr, session)

    if screen_rows < required_rows or screen_columns < required_columns:
        warning = (
            f"Terminal too small: need {required_columns}x{required_rows}, "
            f"have {screen_columns}x{screen_rows}"
        )
        _safe_addnstr(
            stdscr,
            max(1, screen_rows // 2),
            0,
            warning,
            max(0, screen_columns - 1),
            curses.A_BOLD,
        )
        stdscr.refresh()
        return False

    # Python builds backed by narrow-character ncurses interpret Unicode box
    # glyphs as attribute bits. ACS values provide terminal-native line drawing
    # on ncurses and PDCurses while Maze remains the source of the layout.
    for row, line in enumerate(maze_rows, start=1):
        for column, character in enumerate(line):
            wall_character = WALL_CHARACTERS.get(character)
            output = (
                getattr(curses, wall_character, FALLBACK_WALL_CHARACTERS[character])
                if wall_character
                else character
            )
            with suppress(curses.error):
                stdscr.addch(row, column, output)

    if session.escaped:
        footer = (
            f"Escaped in {format_duration(session.timer.elapsed)} - "
            "R: play again, S: change size, Q: quit"
        )
    elif session.timer.paused:
        footer = "Paused - press P to resume (R/S/Q are still available)"
        _draw_banner(stdscr, "PAUSED - P to resume")
    else:
        footer = "Arrow keys: move | P: pause | S: size | R: restart | Q: quit"

    _safe_addnstr(
        stdscr,
        len(maze_rows) + 1,
        0,
        footer,
        max(0, screen_columns - 1),
    )
    stdscr.refresh()
    return True


def choose_size(
    stdscr: curses.window,
    rows: int,
    columns: int,
) -> tuple[int, int] | None:
    """Show a keyboard-driven maze-size dialog."""
    selected_rows = rows
    selected_columns = columns
    stdscr.timeout(-1)

    try:
        while True:
            stdscr.erase()
            screen_rows, screen_columns = stdscr.getmaxyx()
            _safe_addnstr(
                stdscr,
                0,
                0,
                " Change maze size ".ljust(screen_columns),
                screen_columns,
                curses.A_REVERSE,
            )
            lines = (
                f"Rows: {selected_rows}    Columns: {selected_columns}",
                "Up/Down: rows    Left/Right: columns",
                "Enter: start new game    Esc: cancel",
            )
            first_row = max(1, screen_rows // 2 - 1)
            for offset, line in enumerate(lines):
                column = max(0, (screen_columns - len(line)) // 2)
                _safe_addnstr(
                    stdscr,
                    first_row + offset,
                    column,
                    line,
                    max(0, screen_columns - column - 1),
                    curses.A_BOLD if offset == 0 else 0,
                )
            stdscr.refresh()

            key = stdscr.getch()
            if key == curses.KEY_UP:
                selected_rows += 1
            elif key == curses.KEY_DOWN:
                selected_rows = max(MIN_MAZE_SIZE, selected_rows - 1)
            elif key == curses.KEY_RIGHT:
                selected_columns += 1
            elif key == curses.KEY_LEFT:
                selected_columns = max(MIN_MAZE_SIZE, selected_columns - 1)
            elif key in (curses.KEY_ENTER, 10, 13):
                return selected_rows, selected_columns
            elif key == ESCAPE_KEY:
                return None
    finally:
        stdscr.timeout(REFRESH_INTERVAL_MS)


def _play(stdscr: curses.window, rows: int, columns: int) -> list[float]:
    with suppress(curses.error):
        curses.curs_set(0)
    stdscr.keypad(True)  # noqa: FBT003 - curses API requires a positional bool
    stdscr.timeout(REFRESH_INTERVAL_MS)
    session = GameSession(rows, columns)

    while True:
        fits = draw(stdscr, session)
        key = stdscr.getch()

        if key in (ord("q"), ord("Q")):
            return session.completed_times
        if key in (ord("r"), ord("R")):
            session.restart()
            continue
        if key in (ord("s"), ord("S")):
            resume_after_dialog = session.timer.running and not session.timer.paused
            if resume_after_dialog:
                session.timer.pause()
            size = choose_size(stdscr, session.rows, session.columns)
            if size is not None:
                session.restart(*size)
            elif resume_after_dialog:
                session.timer.resume()
            continue
        if key in (ord("p"), ord("P")) and not session.escaped:
            if session.timer.paused:
                session.timer.resume()
            else:
                session.timer.pause()
            continue

        if (
            fits
            and not session.timer.paused
            and not session.escaped
            and key in KEY_DIRECTIONS
        ):
            session.maze.move(KEY_DIRECTIONS[key])
            session.check_for_escape()


def format_results(laps: Iterable[float]) -> str:
    lap_list = list(laps)
    if not lap_list:
        return "You did not complete a game.\nGoodbye!"
    if len(lap_list) == 1:
        return f"You played 1 game that took {format_duration(lap_list[0])}.\nGoodbye!"
    average = sum(lap_list) / len(lap_list)
    return (
        f"You played {len(lap_list)} games with an average time of "
        f"{format_duration(average)}.\nGoodbye!"
    )


def play(rows: int, columns: int) -> None:
    # Curses needs the user's native locale before it can calculate and render
    # the width of the Unicode box-drawing characters used by the maze.
    locale.setlocale(locale.LC_ALL, "")
    completed_times = curses.wrapper(_play, rows, columns)
    sys.stdout.write(f"{format_results(completed_times)}\n")
