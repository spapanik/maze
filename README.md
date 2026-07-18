# maze game

A terminal maze game with an ncurses TUI. Move the `*` to the `X`, while the
top bar keeps the current time and completed-game statistics visible.

Run it with:

```console
maze
```

Choose a maze size with `--rows` and `--columns`:

```console
maze --rows 12 --columns 20
```

## Controls

- Arrow keys: move through the maze
- `P`: pause or resume; paused time is not included in the result
- `R`: restart with the current size
- `S`: open the size picker; use the arrow keys and press Enter to apply
- `Q`: quit

The top bar shows the current state and elapsed time. After the first completed
game it also shows the game count, best time, and average time for the session.

## Platform support

Linux and macOS use Python's standard ncurses module. On Windows, installing
the project automatically installs `windows-curses`, which provides the same
API using PDCurses. Run the game in a normal interactive terminal such as
Windows Terminal, Terminal.app, or a Linux terminal emulator.

[![lint][lint_badge]][lint_url]
[![tests][tests_badge]][tests_url]
[![build automation: yam][yam_badge]][yam_url]
[![Lint: ruff][ruff_badge]][ruff_url]

[lint_badge]: https://github.com/spapanik/maze/actions/workflows/lint.yml/badge.svg
[lint_url]: https://github.com/spapanik/maze/actions/workflows/lint.yml
[tests_badge]: https://github.com/spapanik/maze/actions/workflows/tests.yml/badge.svg
[tests_url]: https://github.com/spapanik/maze/actions/workflows/tests.yml
[yam_badge]: https://img.shields.io/badge/build%20automation-yamk-success
[yam_url]: https://github.com/spapanik/yamk
[ruff_badge]: https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/charliermarsh/ruff/main/assets/badge/v1.json
[ruff_url]: https://github.com/charliermarsh/ruff
