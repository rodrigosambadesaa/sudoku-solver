"""Deterministic unit and property-based regression tests (stdlib unittest)."""

import random
import unittest

from sudoku_solver import is_valid_solution, iter_solutions, parse_board, solve_all


class SolverTests(unittest.TestCase):
    def test_9x9_known_answer(self):
        puzzle = parse_board("""530070000
600195000
098000060
800060003
400803001
700020006
060000280
000419005
000080079""")
        expected = parse_board("""534678912
672195348
198342567
859761423
426853791
713924856
961537284
287419635
345286179""")
        self.assertEqual(solve_all(puzzle), [expected])
        self.assertTrue(is_valid_solution(puzzle, expected))
        self.assertEqual(puzzle[0][2], 0, "Input must never be modified")

    def test_four_by_four_empty_enumerates_all_288(self):
        puzzle = [[0] * 4 for _ in range(4)]
        answers = solve_all(puzzle)
        self.assertEqual(len(answers), 288)
        self.assertEqual(len({tuple(v for row in a for v in row) for a in answers}), 288)
        self.assertTrue(all(is_valid_solution(puzzle, answer) for answer in answers))
        self.assertEqual(len(solve_all(puzzle, max_solutions=2)), 2)

    def test_2x2_rectangular_boxes(self):
        puzzle = [[0, 0], [0, 0]]
        self.assertEqual(len(solve_all(puzzle, box_shape=(1, 2))), 2)
        self.assertEqual(len(solve_all(puzzle, box_shape=(2, 1))), 2)

    def test_bad_inputs(self):
        for grid in ([], [[1, 2], [3]], [[True]], [[-1]], [[2]], [[1, 1], [0, 0]],
                     [[1, 2, 3]] * 3, [[0] * 6 for _ in range(6)]):
            with self.subTest(grid=grid), self.assertRaises(ValueError):
                list(iter_solutions(grid))
        with self.assertRaises(ValueError):
            list(iter_solutions([[0] * 4 for _ in range(4)], max_solutions=0))
        with self.assertRaises(ValueError):
            list(iter_solutions([[0] * 6 for _ in range(6)], box_shape=(2, 2)))
        self.assertFalse(is_valid_solution([[0]], [[0]]))

    def test_consistent_but_unsatisfiable(self):
        puzzle = [[0, 0, 1, 4], [0, 0, 2, 0], [0, 0, 0, 0], [0, 4, 0, 3]]
        self.assertEqual(solve_all(puzzle), [])

    def test_parser(self):
        self.assertEqual(parse_board("[ [1, 0], [0, 2] ]"), [[1, 0], [0, 2]])
        self.assertEqual(parse_board("1 0\n0 2"), [[1, 0], [0, 2]])
        self.assertEqual(parse_board("10\n02"), [[1, 0], [0, 2]])
        self.assertEqual(parse_board(".2.1"), [[0, 2], [0, 1]])
        self.assertEqual(parse_board("A" + "." * 255)[0][0], 10)
        with self.assertRaises(ValueError):
            parse_board("invalid")
        with self.assertRaises(ValueError):
            parse_board("123")

    def test_sizes_up_to_100_and_rectangular_boxes(self):
        for h, w in ((1, 1), (1, 2), (2, 3), (3, 3), (4, 4), (5, 5), (6, 6), (10, 10)):
            n = h * w
            solved = [[(r * w + r // h + c) % n + 1 for c in range(n)] for r in range(n)]
            self.assertTrue(is_valid_solution([[0] * n for _ in range(n)], solved, box_shape=(h, w)))
            # Completed board should return itself in constant-depth DFS.
            self.assertEqual(next(iter_solutions(solved, box_shape=(h, w))), solved)
            if n <= 36:
                # One blank per row; row constraints force a unique solution.
                puzzle = [row.copy() for row in solved]
                for r in range(n):
                    puzzle[r][(r * 7) % n] = 0
                self.assertEqual(solve_all(puzzle, box_shape=(h, w)), [solved])

    def test_property_random_removals(self):
        rng = random.Random(20261013)
        # Generate random but always valid complete boards by band/stack/digit permutations.
        for h, w in ((2, 2), (2, 3), (3, 3)):
            n = h * w
            for _ in range(1000):
                base = [[(r * w + r // h + c) % n + 1 for c in range(n)] for r in range(n)]
                mapped = list(range(1, n + 1))
                rng.shuffle(mapped)
                transformed = [[mapped[x - 1] for x in row] for row in base]
                puzzle = [row.copy() for row in transformed]
                for i in rng.sample(range(n * n), max(1, n * n // 3)):
                    puzzle[i // n][i % n] = 0
                found = next(iter_solutions(puzzle, box_shape=(h, w)))
                self.assertTrue(is_valid_solution(puzzle, found, box_shape=(h, w)))


if __name__ == "__main__":
    unittest.main()
