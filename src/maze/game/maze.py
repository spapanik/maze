from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from secrets import choice, randbelow
from typing import TYPE_CHECKING, Self

from maze.lib.constants import Direction

if TYPE_CHECKING:
    from collections.abc import Iterator

corners = {
    Direction(0): " ",
    Direction.LEFT: "─",
    Direction.RIGHT: "─",
    Direction.LEFT | Direction.RIGHT: "─",
    Direction.DOWN: "│",
    Direction.DOWN | Direction.LEFT: "┐",
    Direction.DOWN | Direction.RIGHT: "┌",
    Direction.DOWN | Direction.LEFT | Direction.RIGHT: "┬",
    Direction.UP: "│",
    Direction.UP | Direction.LEFT: "┘",
    Direction.UP | Direction.RIGHT: "└",
    Direction.UP | Direction.LEFT | Direction.RIGHT: "┴",
    Direction.UP | Direction.DOWN: "│",
    Direction.UP | Direction.DOWN | Direction.LEFT: "┤",
    Direction.UP | Direction.DOWN | Direction.RIGHT: "├",
    Direction.UP | Direction.DOWN | Direction.LEFT | Direction.RIGHT: "┼",
}
walls = {
    Direction.UP: "─",
    Direction.LEFT: "│",
}
all_directions = Direction.UP | Direction.DOWN | Direction.LEFT | Direction.RIGHT


@dataclass(frozen=True, order=True, slots=True)
class Position:
    row: int
    column: int

    def up(self) -> Self:
        return self.__class__(self.row - 1, self.column)

    def down(self) -> Self:
        return self.__class__(self.row + 1, self.column)

    def left(self) -> Self:
        return self.__class__(self.row, self.column - 1)

    def right(self) -> Self:
        return self.__class__(self.row, self.column + 1)


class Maze:
    cursor = "*"
    end = "X"

    def __init__(
        self,
        rows: int,
        columns: int,
    ) -> None:
        self.rows = rows
        self.columns = columns
        self.position = Position(0, 0)
        self.target = Position(rows - 1, columns - 1)
        self.matrix = self.initialize_matrix()

    def __str__(self) -> str:
        return "".join(
            string
            for coordinates in product(
                range(2 * self.rows + 1),
                range(2 * self.columns + 1),
            )
            for string in self.cell_to_str(coordinates)
        )

    def cell_to_str(self, coordinates: tuple[int, int]) -> Iterator[str]:
        x = coordinates[0]
        y = coordinates[1]
        cell = Position(x // 2, y // 2)

        if x % 2 == y % 2 == 1:
            # Cells
            yield " "
            match cell:
                case self.position:
                    yield self.cursor
                case self.target:
                    yield self.end
                case _:
                    yield " "
            yield " "

        elif x % 2 == 0 and y % 2 == 1:
            # Horizontal walls
            if Direction.UP in self.matrix.get(cell, all_directions):
                yield walls[Direction.UP] * 3
            else:
                yield " " * 3

        elif x % 2 == 1 and y % 2 == 0:
            # Vertical walls
            if Direction.LEFT in self.matrix.get(cell, all_directions):
                yield walls[Direction.LEFT]
            else:
                yield " "

        elif x == y == 0:
            # Top left corner
            yield corners[Direction.DOWN | Direction.RIGHT]
        elif x == 0 and y == 2 * self.columns:
            # Top right corner
            yield corners[Direction.DOWN | Direction.LEFT]
        elif x == 2 * self.rows and y == 0:
            # Bottom left corner
            yield corners[Direction.UP | Direction.RIGHT]
        elif x == 2 * self.rows and y == 2 * self.columns:
            # Bottom right corner
            yield corners[Direction.UP | Direction.LEFT]
        elif x == 0:
            # Top border
            direction = Direction.RIGHT | Direction.LEFT
            if Direction.LEFT in self.matrix[cell]:
                direction |= Direction.DOWN
            yield corners[direction]
        elif y == 0:
            # Left border
            direction = Direction.UP | Direction.DOWN
            if Direction.UP in self.matrix[cell]:
                direction |= Direction.RIGHT
            yield corners[direction]
        elif x == 2 * self.rows:
            # Bottom border
            direction = Direction.RIGHT | Direction.LEFT
            if Direction.LEFT in self.matrix[cell.up()]:
                direction |= Direction.UP
            yield corners[direction]
        elif y == 2 * self.columns:
            # Right border
            direction = Direction.UP | Direction.DOWN
            if Direction.UP in self.matrix[cell.left()]:
                direction |= Direction.LEFT
            yield corners[direction]
        else:
            # Intersections inside the maze
            direction = Direction(0)
            if Direction.UP in self.matrix[cell]:
                direction |= Direction.RIGHT
            if Direction.UP in self.matrix[cell.left()]:
                direction |= Direction.LEFT
            if Direction.LEFT in self.matrix[cell]:
                direction |= Direction.DOWN
            if Direction.LEFT in self.matrix[cell.up()]:
                direction |= Direction.UP
            yield corners[direction]

        if y == 2 * self.columns:
            yield "\n"

    def move(self, direction: Direction) -> None:
        if direction in self.matrix[self.position]:
            return

        match direction:
            case Direction.UP:
                self.position = self.position.up()
            case Direction.DOWN:
                self.position = self.position.down()
            case Direction.LEFT:
                self.position = self.position.left()
            case Direction.RIGHT:
                self.position = self.position.right()

    def initialize_matrix(self) -> dict[Position, Direction]:
        matrix = {
            Position(row, column): all_directions
            for row in range(self.rows)
            for column in range(self.columns)
        }
        cell = Position(randbelow(self.rows), randbelow(self.columns))
        cell_stack = [cell]

        visited_cells = 1
        while visited_cells < len(matrix):
            cell = cell_stack[-1]

            available_directions = []
            if matrix.get(cell.up(), Direction(0)) == all_directions:
                available_directions.append(Direction.UP)
            if matrix.get(cell.down(), Direction(0)) == all_directions:
                available_directions.append(Direction.DOWN)
            if matrix.get(cell.left(), Direction(0)) == all_directions:
                available_directions.append(Direction.LEFT)
            if matrix.get(cell.right(), Direction(0)) == all_directions:
                available_directions.append(Direction.RIGHT)

            if available_directions:
                go = choice(available_directions)
                visited_cells += 1
                next_cell: Position
                match go:
                    case Direction.UP:
                        next_cell = cell.up()
                        matrix[cell] ^= Direction.UP
                        matrix[next_cell] ^= Direction.DOWN
                    case Direction.DOWN:
                        next_cell = cell.down()
                        matrix[cell] ^= Direction.DOWN
                        matrix[next_cell] ^= Direction.UP
                    case Direction.LEFT:
                        next_cell = cell.left()
                        matrix[cell] ^= Direction.LEFT
                        matrix[next_cell] ^= Direction.RIGHT
                    case Direction.RIGHT:
                        next_cell = cell.right()
                        matrix[cell] ^= Direction.RIGHT
                        matrix[next_cell] ^= Direction.LEFT
                cell_stack.append(next_cell)
            else:
                cell_stack.pop()
        return matrix

    def player_escaped(self) -> bool:
        return self.position == self.target
