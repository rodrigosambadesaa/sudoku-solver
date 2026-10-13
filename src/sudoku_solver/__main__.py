"""Command-line entry point: python -m sudoku_solver."""

from __future__ import annotations

import argparse
import json
import sys

from . import format_board, iter_solutions, parse_board


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Solve a Sudoku of any NxN size; enumerate all solutions by default.")
    parser.add_argument("file", nargs="?", default="-", help="Input path (default: stdin)")
    parser.add_argument("--box", metavar="HxW", help="Box dimensions, e.g. 2x3 for a 6x6 Sudoku")
    parser.add_argument("--max-solutions", type=int, default=None, help="Stop after this many solutions")
    parser.add_argument("--json", action="store_true", help="Emit each solution as one JSON array per line (JSONL)")
    args = parser.parse_args(argv)
    try:
        if args.box:
            parts = args.box.lower().split("x")
            if len(parts) != 2:
                raise ValueError("--box format must be HxW")
            box = (int(parts[0]), int(parts[1]))
        else:
            box = None
        with (sys.stdin if args.file == "-" else open(args.file, encoding="utf-8")) as stream:
            board = parse_board(stream.read())
        solutions = iter_solutions(board, box_shape=box, max_solutions=args.max_solutions)
        count = 0
        for count, solution in enumerate(solutions, 1):
            if args.json:
                print(json.dumps(solution, separators=(",", ":")))
            else:
                if count > 1:
                    print()
                print(f"Solution {count}:\n{format_board(solution)}")
        if not args.json:
            print(f"\nSolutions found: {count}", file=sys.stderr)
            if args.max_solutions is not None and count == args.max_solutions:
                print("Result capped; additional solutions may exist.", file=sys.stderr)
        return 0 if count else 1
    except (OSError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
