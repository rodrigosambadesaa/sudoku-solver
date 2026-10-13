"""Check public Sudoku Challenge puzzles and reference answers (network required).

Source: https://github.com/sowpati/sudoku-challenge
Three CSVs, each containing 1,000 externally supplied quiz/answer pairs.
No dataset is redistributed in this repository.
"""

from __future__ import annotations

import argparse
import csv
import io
import time
from urllib.request import urlopen

from sudoku_solver import is_valid_solution, iter_solutions, parse_board

BASE = "https://raw.githubusercontent.com/sowpati/sudoku-challenge/master/"
DATASETS = ("easy.csv", "hard.csv", "harder.csv")


def run(limit_per_file: int = 1000) -> None:
    if limit_per_file < 1:
        raise ValueError("limit_per_file must be positive")
    total = 0
    multiple = 0
    start = time.perf_counter()
    for dataset in DATASETS:
        with urlopen(BASE + dataset, timeout=45) as response:  # noqa: S310: fixed HTTPS GitHub URL
            contents = response.read().decode("utf-8-sig")
        rows = csv.DictReader(io.StringIO(contents))
        checked = 0
        for entry in rows:
            if checked >= limit_per_file:
                break
            quiz = entry.get("puzzles") or entry.get("hard") or entry.get("harder")
            answer = entry.get("solutions")
            if not quiz or not answer:
                raise AssertionError(f"Missing puzzle/answer in {dataset}, row {checked + 2}")
            puzzle = parse_board(quiz)
            expected = parse_board(answer)
            if not is_valid_solution(puzzle, expected):
                raise AssertionError(f"Dataset has invalid reference answer: {dataset}:{checked + 2}")
            iterator = iter_solutions(puzzle, max_solutions=2)
            first = next(iterator, None)
            second = next(iterator, None)
            if first is None or not is_valid_solution(puzzle, first):
                raise AssertionError(f"Solver gave no valid answer: {dataset}:{checked + 2}")
            if second is not None:
                multiple += 1
                if not is_valid_solution(puzzle, second) or second == first:
                    raise AssertionError(f"Invalid or duplicate solution: {dataset}:{checked + 2}")
            elif first != expected:
                raise AssertionError(f"Unique answer differs from reference: {dataset}:{checked + 2}")
            checked += 1
        print(f"{dataset}: {checked} puzzles passed", flush=True)
        if checked < limit_per_file:
            raise AssertionError(f"Only {checked} puzzles available in {dataset}")
        total += checked
    print(f"PASS: {total} public puzzles; {multiple} with multiple completions; {time.perf_counter() - start:.2f}s")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit-per-file", type=int, default=1000)
    arguments = parser.parse_args()
    run(arguments.limit_per_file)
