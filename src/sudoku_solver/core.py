"""Exact, dependency-free Sudoku solver with lazy solution enumeration."""

from __future__ import annotations

from math import isqrt
from typing import Iterator, Sequence

Board = list[list[int]]


def _prepare(board: Sequence[Sequence[int]], box_shape: tuple[int, int] | None):
    """Validate initial clues and construct immutable shape metadata."""
    if isinstance(board, (str, bytes)) or not isinstance(board, Sequence) or not board:
        raise ValueError("Board must be a nonempty square matrix of integers")
    n = len(board)
    if box_shape is None:
        side = isqrt(n)
        if side * side != n:
            raise ValueError(f"Size {n} requires an explicit box_shape, e.g. (2, 3) for 6x6")
        height = width = side
    else:
        if (not isinstance(box_shape, tuple) or len(box_shape) != 2 or
                any(isinstance(x, bool) or not isinstance(x, int) or x <= 0 for x in box_shape)):
            raise ValueError("box_shape must be a tuple of two positive integers")
        height, width = box_shape
        if height * width != n:
            raise ValueError("box_shape height * width must equal the board size")

    values: list[int] = []
    for r, row in enumerate(board):
        if isinstance(row, (str, bytes)) or not isinstance(row, Sequence) or len(row) != n:
            raise ValueError(f"Row {r + 1} must contain exactly {n} integers")
        for c, value in enumerate(row):
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= n:
                raise ValueError(f"Cell ({r + 1}, {c + 1}) must be an integer from 0 to {n}")
            values.append(value)

    full = (1 << n) - 1
    row_of = [i // n for i in range(n * n)]
    col_of = [i % n for i in range(n * n)]
    box_of = [(r // height) * (n // width) + (c // width)
              for r in range(n) for c in range(n)]
    rows = [0] * n
    cols = [0] * n
    boxes = [0] * n
    empties: list[int] = []
    for i, value in enumerate(values):
        if value == 0:
            empties.append(i)
            continue
        bit = 1 << (value - 1)
        r, c, b = row_of[i], col_of[i], box_of[i]
        if rows[r] & bit or cols[c] & bit or boxes[b] & bit:
            raise ValueError(f"Conflicting given {value} at ({r + 1}, {c + 1})")
        rows[r] |= bit
        cols[c] |= bit
        boxes[b] |= bit
    return n, full, values, empties, row_of, col_of, box_of, rows, cols, boxes


def iter_solutions(
    board: Sequence[Sequence[int]],
    *,
    box_shape: tuple[int, int] | None = None,
    max_solutions: int | None = None,
) -> Iterator[Board]:
    """Yield every valid completion, without changing *board*.

    Defaults to exhaustive enumeration. Set max_solutions to stop early. Clue
    conflicts or malformed inputs raise ValueError; unsatisfiable puzzles yield
    no solutions. This uses an explicit DFS stack (no recursion depth limit).
    """
    if max_solutions is not None and (
        isinstance(max_solutions, bool) or not isinstance(max_solutions, int) or max_solutions < 1
    ):
        raise ValueError("max_solutions must be a positive integer or None")
    n, full, cells, empties, row_of, col_of, box_of, rows, cols, boxes = _prepare(board, box_shape)

    def search() -> Iterator[Board]:
        trail: list[tuple[int, int]] = []
        # [decision cell, alternatives bitmask, trail length before the decision]
        stack: list[list[int]] = []
        produced = 0

        def assign(i: int, bit: int) -> None:
            cells[i] = bit.bit_length()
            rows[row_of[i]] |= bit
            cols[col_of[i]] |= bit
            boxes[box_of[i]] |= bit
            trail.append((i, bit))

        def rollback(depth: int) -> None:
            while len(trail) > depth:
                i, bit = trail.pop()
                cells[i] = 0
                rows[row_of[i]] ^= bit
                cols[col_of[i]] ^= bit
                boxes[box_of[i]] ^= bit

        def scan() -> tuple[int, int, bool]:
            """Propagate naked/hidden singles; return (index, options, solved)."""
            while True:
                best_i, best_options, best_size = -1, 0, n + 1
                # Bits that appear in >=1 / >=2 empty cells per unit.
                once_r, many_r = [0] * n, [0] * n
                once_c, many_c = [0] * n, [0] * n
                once_b, many_b = [0] * n, [0] * n
                candidates: dict[int, int] = {}
                single = None
                for i in empties:
                    if cells[i]:
                        continue
                    r, c, b = row_of[i], col_of[i], box_of[i]
                    options = full & ~(rows[r] | cols[c] | boxes[b])
                    if not options:
                        return -1, 0, False
                    count = options.bit_count()
                    if count == 1:
                        single = (i, options)
                        break
                    candidates[i] = options
                    if count < best_size:
                        best_i, best_options, best_size = i, options, count
                    many_r[r] |= once_r[r] & options
                    many_c[c] |= once_c[c] & options
                    many_b[b] |= once_b[b] & options
                    once_r[r] |= options
                    once_c[c] |= options
                    once_b[b] |= options
                if single is not None:
                    assign(*single)
                    continue
                if best_i == -1:
                    return -1, 0, True

                # Missing digits without any candidate make a board impossible;
                # digits occurring once in a unit are forced (hidden singles).
                forced = None
                for used, once, many, membership in (
                    (rows, once_r, many_r, row_of),
                    (cols, once_c, many_c, col_of),
                    (boxes, once_b, many_b, box_of),
                ):
                    for unit in range(n):
                        missing = full & ~used[unit]
                        if missing & ~once[unit]:
                            return -1, 0, False
                        unique = missing & once[unit] & ~many[unit]
                        if unique:
                            bit = unique & -unique
                            forced = next((i, bit) for i, opts in candidates.items()
                                          if membership[i] == unit and opts & bit)
                            break
                    if forced:
                        break
                if forced:
                    assign(*forced)
                    continue
                return best_i, best_options, False

        def advance() -> bool:
            """Backtrack to the next untried alternative, if any."""
            while stack:
                i, alternatives, depth = stack[-1]
                rollback(depth)
                if alternatives:
                    bit = alternatives & -alternatives
                    stack[-1][1] = alternatives ^ bit
                    assign(i, bit)
                    return True
                stack.pop()
            return False

        while True:
            i, options, solved = scan()
            if solved:
                produced += 1
                yield [cells[r * n:(r + 1) * n] for r in range(n)]
                if max_solutions is not None and produced >= max_solutions:
                    return
            elif i >= 0:
                bit = options & -options
                stack.append([i, options ^ bit, len(trail)])
                assign(i, bit)
                continue
            if not advance():
                return

    return search()


def solve_all(
    board: Sequence[Sequence[int]],
    *,
    box_shape: tuple[int, int] | None = None,
    max_solutions: int | None = None,
) -> list[Board]:
    """Collect solutions in memory. Prefer iter_solutions for large result sets."""
    return list(iter_solutions(board, box_shape=box_shape, max_solutions=max_solutions))


def is_valid_solution(
    puzzle: Sequence[Sequence[int]],
    solution: Sequence[Sequence[int]],
    *,
    box_shape: tuple[int, int] | None = None,
) -> bool:
    """Independently check that a completion respects all Sudoku constraints."""
    try:
        n, _, original, _, _, _, _, _, _, _ = _prepare(puzzle, box_shape)
        if len(solution) != n or any(len(row) != n for row in solution):
            return False
        final = [cell for row in solution for cell in row]
        if any(old != 0 and old != new for old, new in zip(original, final)):
            return False
        _, _, _, blanks, _, _, _, _, _, _ = _prepare(solution, box_shape)
        return not blanks
    except (TypeError, ValueError):
        return False
