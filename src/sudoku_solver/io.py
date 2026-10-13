"""Load Sudoku boards in readable JSON, numeric, or compact notation."""

from __future__ import annotations

import json
from math import isqrt

_SYMBOLS = "123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def _square(tokens: list[int]) -> list[list[int]]:
    n = isqrt(len(tokens))
    if n == 0 or n * n != len(tokens):
        raise ValueError("Expected N*N cell values for a square grid")
    return [tokens[i:i + n] for i in range(0, len(tokens), n)]


def parse_board(text: str) -> list[list[int]]:
    """Parse a grid: JSON matrix, whitespace integers, or compact 1-9A-Z/0/. notation.

    Compact notation is supported up to 35x35; larger boards should use
    whitespace-separated decimal integers or a JSON matrix.
    """
    if not isinstance(text, str) or not text.strip():
        raise ValueError("Empty puzzle")
    stripped = text.strip()
    if stripped.startswith("["):
        try:
            return json.loads(stripped)
        except json.JSONDecodeError as exc:
            raise ValueError("Invalid JSON grid") from exc

    words = stripped.replace(",", " ").split()
    # If each token is a row string of length >= 2, use compact notation.
    # One token can also encode a whole board.
    if len(words) == 1 or (len(words) > 1 and len(words) == len(words[0])
                           and all(len(w) == len(words[0]) for w in words)):
        compact = "".join(words).upper()
        n = isqrt(len(compact))
        if n * n == len(compact) and n <= len(_SYMBOLS):
            allowed = set(_SYMBOLS[:n]) | {"0", "."}
            if not set(compact) <= allowed:
                raise ValueError(f"Invalid symbol for {n}x{n} Sudoku")
            return _square([0 if c in ".0" else _SYMBOLS.index(c) + 1 for c in compact])
    if len(words) == 1:
        raise ValueError("Compact notation needs exactly N*N symbols")
    try:
        return _square([int(word) if word != "." else 0 for word in words])
    except ValueError as exc:
        raise ValueError("Use JSON, whitespace-separated integers or compact symbols") from exc


def format_board(board: list[list[int]]) -> str:
    """Text representation that also works for large numbers (> 35)."""
    width = len(str(len(board)))
    return "\n".join(" ".join(f"{v:>{width}}" for v in row) for row in board)
