"""
Norvig-style Sudoku solver (constraint propagation + search)

Based on the approach described by Peter Norvig:
https://norvig.com/sudoku.html

This file is intentionally separate from main.py because it is not
student-authored code. It is used for comparison and benchmarking.
"""

# -------------------------------------------------------------------------
# Build Sudoku Structures
# -------------------------------------------------------------------------

def build_sudoku_structures():
    row_labels = "ABCDEFGHI"
    column_labels = "123456789"

    squares = []
    for row_label in row_labels:
        for column_label in column_labels:
            squares.append(row_label + column_label)

    unit_list = []

    # Row units
    for row_label in row_labels:
        unit = []
        for column_label in column_labels:
            unit.append(row_label + column_label)
        unit_list.append(unit)

    # Column units
    for column_label in column_labels:
        unit = []
        for row_label in row_labels:
            unit.append(row_label + column_label)
        unit_list.append(unit)

    # Box units
    row_groups = ["ABC", "DEF", "GHI"]
    column_groups = ["123", "456", "789"]
    for row_group in row_groups:
        for column_group in column_groups:
            unit = []
            for row_label in row_group:
                for column_label in column_group:
                    unit.append(row_label + column_label)
            unit_list.append(unit)

    units = {}
    for square in squares:
        units_for_square = []
        for unit in unit_list:
            if square in unit:
                units_for_square.append(unit)
        units[square] = units_for_square

    peers = {}
    for square in squares:
        peer_set = set()
        for unit in units[square]:
            for other_square in unit:
                if other_square != square:
                    peer_set.add(other_square)
        peers[square] = peer_set

    return squares, unit_list, units, peers


SQUARES, UNIT_LIST, UNITS, PEERS = build_sudoku_structures()

# -------------------------------------------------------------------------
# Stats Helper
# -------------------------------------------------------------------------

def make_stats():
    return {
        "assignments": 0,
        "eliminations": 0,
        "search_nodes": 0,
        "contradictions": 0
    }

# -------------------------------------------------------------------------
# Core Constraint Propagation
# -------------------------------------------------------------------------

def parse_grid_to_candidates(puzzle_string, stats):
    candidates = {}
    for square in SQUARES:
        candidates[square] = "123456789"

    index = 0
    for square in SQUARES:
        ch = puzzle_string[index]
        index += 1

        if ch == "0" or ch == ".":
            continue

        if assign(candidates, square, ch, stats) is None:
            return None

    return candidates


def assign(candidates, square, digit_to_keep, stats):
    stats["assignments"] += 1

    other_digits = ""
    for digit in candidates[square]:
        if digit != digit_to_keep:
            other_digits += digit

    for digit in other_digits:
        if eliminate(candidates, square, digit, stats) is None:
            return None

    return candidates


def eliminate(candidates, square, digit_to_remove, stats):
    if digit_to_remove not in candidates[square]:
        return candidates

    stats["eliminations"] += 1
    candidates[square] = candidates[square].replace(digit_to_remove, "")

    if len(candidates[square]) == 0:
        stats["contradictions"] += 1
        return None

    if len(candidates[square]) == 1:
        only_digit = candidates[square]
        for peer_square in PEERS[square]:
            if eliminate(candidates, peer_square, only_digit, stats) is None:
                return None

    for unit in UNITS[square]:
        places_for_digit = []
        for unit_square in unit:
            if digit_to_remove in candidates[unit_square]:
                places_for_digit.append(unit_square)

        if len(places_for_digit) == 0:
            stats["contradictions"] += 1
            return None

        if len(places_for_digit) == 1:
            only_place = places_for_digit[0]
            if assign(candidates, only_place, digit_to_remove, stats) is None:
                return None

    return candidates

# -------------------------------------------------------------------------
# Depth-First Search
# -------------------------------------------------------------------------

def search(candidates, stats):
    if candidates is None:
        return None

    stats["search_nodes"] += 1

    solved = True
    for square in SQUARES:
        if len(candidates[square]) != 1:
            solved = False
            break
    if solved:
        return candidates

    best_square = None
    best_length = 10
    for square in SQUARES:
        length_here = len(candidates[square])
        if length_here > 1 and length_here < best_length:
            best_length = length_here
            best_square = square

    for digit in candidates[best_square]:
        candidates_copy = {}
        for key in candidates:
            candidates_copy[key] = candidates[key]

        attempt = assign(candidates_copy, best_square, digit, stats)
        result = search(attempt, stats)
        if result is not None:
            return result

    return None

# -------------------------------------------------------------------------
# Public API
# -------------------------------------------------------------------------

def solve_norvig(puzzle_string, stats=None):
    """
    Input: 81-character string (digits with 0 or . for empty)
    Output: 81-character solved string or None
    """
    if stats is None:
        stats = make_stats()

    candidates = parse_grid_to_candidates(puzzle_string, stats)
    result = search(candidates, stats)

    if result is None:
        return None

    output = ""
    for square in SQUARES:
        output += result[square]

    return output