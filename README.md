# Universal Sudoku Solver 🧩

A **pure-Python, dependency-free Sudoku solver** for standard Sudoku boards of any **N×N** size with **H×W** boxes where `H × W = N`. It enumerates **every valid solution by default**, instead of silently picking one.

## Features

- **All solutions:** lazy enumeration (`iter_solutions`), no built-in limit, no duplicate boards; optional `max_solutions` for performance.
- **Any positive board size:** 1×1, 4×4, 9×9, 16×16, 25×25, 36×36, 100×100, etc. Non-square box shapes, such as 2×3 for 6×6, are also supported.
- **Exact algorithm:** constraint propagation (naked/hidden singles), bit masks, minimum-remaining-values (MRV) branching and iterative depth-first backtracking. No heuristic guesses are returned as solved boards.
- **Robust validation:** wrong shapes, values, duplicate givens, and invalid boxes raise descriptive `ValueError`; consistent but impossible puzzles yield no solution; input is never mutated.
- **Standard library only:** Python 3.10+; programmatic API, command-line interface, JSONL output, automated tests and reproducible public-dataset benchmark.

## Install

```bash
git clone https://github.com/rodrigosambadesaa/sudoku-solver.git
cd sudoku-solver
python -m pip install -e .
```

## Command line

Paste a compact puzzle in `puzzle.txt` (`0` or `.` means blank):

```text
530070000
600195000
098000060
800060003
400803001
700020006
060000280
000419005
000080079
```

```bash
sudoku-solver puzzle.txt                     # Prints ALL solutions
python -m sudoku_solver puzzle.txt --json    # One JSON matrix per line, stream-friendly
sudoku-solver puzzle.txt --max-solutions 2   # Stop after two (useful for uniqueness checks)
sudoku-solver puzzle6.txt --box 2x3          # Six-by-six board with 2x3 boxes
cat puzzle.txt | sudoku-solver -
```

Exit codes: `0` ≥1 solution found; `1` no solution; `2` input/read error. `--max-solutions` is optional; omitting it enumerates every solution. When output is capped, the CLI warns that further solutions may exist.

For sizes up to **35×35**, compact notation uses `1`–`9`, `A`–`Z` (10–35), and `0`/`.` for blanks. For any size, use a **JSON integer matrix** or **N² whitespace-separated decimal integers** (values 0–N). Example: a `16×16` uses `A` for 10 and `G` for 16; a `36×36` should use decimal integers.

## Python API

```python
from sudoku_solver import iter_solutions, solve_all, parse_board, is_valid_solution

puzzle = parse_board("530070000600195000098000060800060003400803001700020006060000280000419005000080079")
for solution in iter_solutions(puzzle):
    assert is_valid_solution(puzzle, solution)
    print(solution)

# Only use solve_all when it is safe to hold all solutions in memory.
answers = solve_all(puzzle)
print("Number of solutions:", len(answers))

# No imposed size limit in the API; rectangular boxes require box_shape.
# answers6 = solve_all(board6, box_shape=(2, 3))
```

### Important computational limitation

The program can **represent and validate arbitrarily large square grids**, but exhaustive Sudoku solving is exponential in the worst case. A nearly empty 9×9 or 16×16 can have an astronomical number of completions, so **enumerating all of them may be infeasible** in time/output. `iter_solutions` streams solutions without collecting them in memory. Set `max_solutions=2` to distinguish unique from multiple solutions without a full enumeration. There is no mathematically meaningful promise that a program will terminate quickly for every possible size or underconstrained board.

This project solves **standard Sudoku only** (row, column and box uniqueness), not variants such as diagonal Sudoku, cages, or irregular jigsaw boxes.

## Testing

```bash
python -m unittest discover -s tests -v
python scripts/benchmark_public.py --limit-per-file 1000
```

The optional public benchmark downloads **3,000 puzzle/solution pairs** from [sowpati/sudoku-challenge](https://github.com/sowpati/sudoku-challenge) (`easy.csv`, `hard.csv`, and `harder.csv`), checks that the external reference solution is valid, verifies the solver's returned completions and checks for duplicate answers. Downloads happen **at test time**; the upstream CSV files are not bundled. GitHub Actions runs the unit suite across three Python versions and the full 3,000-puzzle public benchmark on push/PR.

Unit tests also cover all **288 completions of the empty 4×4 Sudoku**, larger sizes including 100×100 solved boards, rectangular boxes, malformed inputs, immutability, and randomized valid board transformations. Passing a finite test suite does not constitute a proof that every conceivable Sudoku input will work; please report any reproducible counterexample as an issue.
