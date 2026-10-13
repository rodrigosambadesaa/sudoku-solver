"""Sudoku solver supporting arbitrary square board sizes and rectangular boxes."""
from .core import is_valid_solution, iter_solutions, solve_all
from .io import format_board, parse_board

__all__ = ["is_valid_solution", "iter_solutions", "solve_all", "format_board", "parse_board"]
