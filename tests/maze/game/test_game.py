from __future__ import annotations

import curses
import locale
from typing import cast
from unittest import mock

import pytest

from maze.game.game import (
    REFRESH_INTERVAL_MS,
    GameSession,
    GameTimer,
    _draw_banner,
    _play,
    _safe_addnstr,
    choose_size,
    draw,
    format_duration,
    format_results,
    play,
)
from maze.game.maze import Maze
from maze.lib.constants import Direction


class ManualClock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now


def test_timer_excludes_paused_time_and_stops() -> None:
    clock = ManualClock()
    timer = GameTimer(clock)

    clock.now = 5.0
    assert timer.elapsed == 5.0

    timer.pause()
    clock.now = 20.0
    assert timer.elapsed == 5.0

    timer.resume()
    clock.now = 23.0
    assert timer.stop() == 8.0

    clock.now = 50.0
    assert timer.elapsed == 8.0


def test_timer_can_stop_while_paused_at_zero() -> None:
    clock = ManualClock()
    timer = GameTimer(clock)

    timer.pause()
    clock.now = 10.0

    assert timer.stop() == 0.0


def test_timer_ignores_redundant_pause_resume_and_stop() -> None:
    clock = ManualClock()
    timer = GameTimer(clock)

    timer.resume()
    timer.pause()
    clock.now = 5.0
    timer.pause()
    assert timer.elapsed == 0.0

    timer.resume()
    clock.now = 7.0
    assert timer.stop() == 2.0

    timer.pause()
    clock.now = 9.0
    assert timer.stop() == 2.0


def test_session_has_no_statistics_before_the_first_escape() -> None:
    session = GameSession(2, 2, ManualClock())

    assert session.best is None
    assert session.average is None


def test_session_records_completed_games_and_statistics() -> None:
    clock = ManualClock()
    session = GameSession(2, 2, clock)
    clock.now = 4.0
    session.maze.position = session.maze.target

    session.check_for_escape()
    session.check_for_escape()

    assert session.completed_times == [4.0]
    assert session.best == 4.0
    assert session.average == 4.0
    assert session.escaped

    session.restart()
    clock.now = 10.0
    session.maze.position = session.maze.target
    session.check_for_escape()

    assert session.completed_times == [4.0, 6.0]
    assert session.best == 4.0
    assert session.average == 5.0


@pytest.mark.parametrize(
    ("seconds", "expected"),
    [
        (0.0, "00:00.0"),
        (65.99, "01:05.9"),
        (3_661.2, "1:01:01.2"),
        (-1.0, "00:00.0"),
    ],
)
def test_format_duration(seconds: float, expected: str) -> None:
    assert format_duration(seconds) == expected


@pytest.mark.parametrize(
    ("times", "expected"),
    [
        ([], "You did not complete a game.\nGoodbye!"),
        ([2.0], "You played 1 game that took 00:02.0.\nGoodbye!"),
        (
            [2.0, 4.0],
            "You played 2 games with an average time of 00:03.0.\nGoodbye!",
        ),
    ],
)
def test_format_results(times: list[float], expected: str) -> None:
    assert format_results(times) == expected


def test_choose_size_uses_arrow_keys_and_restores_refresh_timeout() -> None:
    window = mock.MagicMock()
    window.getmaxyx.return_value = (24, 80)
    window.getch.side_effect = [curses.KEY_UP, curses.KEY_RIGHT, 10]

    selected = choose_size(cast("curses.window", window), 2, 3)

    assert selected == (3, 4)
    assert window.timeout.call_args_list == [
        mock.call(-1),
        mock.call(REFRESH_INTERVAL_MS),
    ]


def test_choose_size_never_goes_below_one_and_can_be_cancelled() -> None:
    window = mock.MagicMock()
    window.getmaxyx.return_value = (24, 80)
    window.getch.side_effect = [curses.KEY_DOWN, ord("x"), curses.KEY_LEFT, 27]

    selected = choose_size(cast("curses.window", window), 1, 1)

    assert selected is None


def test_safe_addnstr_skips_non_positive_widths() -> None:
    window = mock.MagicMock()

    _safe_addnstr(cast("curses.window", window), 0, 0, "text", 0)

    window.addnstr.assert_not_called()


def test_draw_banner_skips_screens_that_cannot_fit_it() -> None:
    window = mock.MagicMock()
    window.getmaxyx.return_value = (2, 2)

    _draw_banner(cast("curses.window", window), "PAUSED")

    window.addnstr.assert_not_called()


def test_draw_shows_statistics_and_the_escape_footer() -> None:
    window = mock.MagicMock()
    window.getmaxyx.return_value = (24, 100)
    clock = ManualClock()
    session = GameSession(2, 2, clock)
    clock.now = 3.0
    session.maze.position = session.maze.target
    session.check_for_escape()

    assert draw(cast("curses.window", window), session)

    text = " ".join(call.args[2] for call in window.addnstr.call_args_list)
    assert "DONE" in text
    assert "Best 00:03.0" in text
    assert "Avg 00:03.0" in text
    assert "Escaped in 00:03.0" in text


def test_draw_shows_top_bar_and_pause_banner() -> None:
    window = mock.MagicMock()
    window.getmaxyx.return_value = (24, 100)
    session = GameSession(2, 2, ManualClock())
    session.timer.pause()

    assert draw(cast("curses.window", window), session)

    text = " ".join(call.args[2] for call in window.addnstr.call_args_list)
    assert "S:Size R:Restart P:Resume Q:Quit" in text
    assert "00:00.0 #0" in text
    assert "PAUSED - P to resume" in text


def test_draw_hides_maze_interior_while_paused() -> None:
    window = mock.MagicMock()
    window.getmaxyx.return_value = (24, 100)
    session = GameSession(2, 2, ManualClock())

    assert draw(cast("curses.window", window), session)
    characters = {call.args[2] for call in window.addch.call_args_list}
    assert Maze.cursor in characters
    assert Maze.end in characters

    window.reset_mock()
    session.timer.pause()

    assert draw(cast("curses.window", window), session)
    characters = {call.args[2] for call in window.addch.call_args_list}
    assert Maze.cursor not in characters
    assert Maze.end not in characters


def test_draw_reports_when_terminal_is_too_small() -> None:
    window = mock.MagicMock()
    window.getmaxyx.return_value = (2, 5)
    session = GameSession(2, 2, ManualClock())

    assert not draw(cast("curses.window", window), session)
    assert any(
        "Terminal too small" in call.args[2] for call in window.addnstr.call_args_list
    )


def test_play_toggles_pause_and_pauses_a_cancelled_size_dialog() -> None:
    window = mock.MagicMock()
    window.getch.side_effect = [ord("p"), ord("p"), ord("s"), ord("q")]
    session = mock.MagicMock()
    session.rows = 2
    session.columns = 3
    session.completed_times = [4.0]
    session.escaped = False
    session.timer.running = True
    session.timer.paused = False

    def pause() -> None:
        session.timer.paused = True

    def resume() -> None:
        session.timer.paused = False

    session.timer.pause.side_effect = pause
    session.timer.resume.side_effect = resume

    with (
        mock.patch("maze.game.game.GameSession", return_value=session),
        mock.patch("maze.game.game.draw", return_value=True),
        mock.patch("maze.game.game.choose_size", return_value=None) as size_dialog,
    ):
        result = _play(cast("curses.window", window), 2, 3)

    assert result == [4.0]
    assert session.timer.pause.call_count == 2
    assert session.timer.resume.call_count == 2
    size_dialog.assert_called_once_with(window, 2, 3)


def test_play_moves_the_player_and_restarts() -> None:
    window = mock.MagicMock()
    window.getch.side_effect = [curses.KEY_UP, -1, ord("r"), ord("q")]
    session = mock.MagicMock()
    session.completed_times = []
    session.escaped = False
    session.timer.paused = False

    with (
        mock.patch("maze.game.game.GameSession", return_value=session),
        mock.patch("maze.game.game.draw", return_value=True),
    ):
        result = _play(cast("curses.window", window), 2, 3)

    assert result == []
    session.maze.move.assert_called_once_with(Direction.UP)
    session.check_for_escape.assert_called_once_with()
    session.restart.assert_called_once_with()


def test_play_size_dialog_while_paused_stays_paused() -> None:
    window = mock.MagicMock()
    window.getch.side_effect = [ord("s"), ord("s"), ord("q")]
    session = mock.MagicMock()
    session.rows = 2
    session.columns = 3
    session.completed_times = []
    session.escaped = False
    session.timer.running = True
    session.timer.paused = True

    with (
        mock.patch("maze.game.game.GameSession", return_value=session),
        mock.patch("maze.game.game.draw", return_value=True),
        mock.patch("maze.game.game.choose_size", side_effect=[(4, 5), None]),
    ):
        _play(cast("curses.window", window), 2, 3)

    session.timer.pause.assert_not_called()
    session.timer.resume.assert_not_called()
    session.restart.assert_called_once_with(4, 5)


def test_play_prints_the_results_after_curses_exits(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with (
        mock.patch("maze.game.game.locale.setlocale") as setlocale,
        mock.patch("maze.game.game.curses.wrapper", return_value=[2.0]) as wrapper,
    ):
        play(3, 4)

    setlocale.assert_called_once_with(locale.LC_ALL, "")
    wrapper.assert_called_once_with(_play, 3, 4)
    out = capsys.readouterr().out
    assert out == "You played 1 game that took 00:02.0.\nGoodbye!\n"
