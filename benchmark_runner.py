import csv
import time

from board import boards
from norvig_solver import solve_norvig, make_stats


def count_given_clues(puzzle_string):
    given = 0
    for ch in puzzle_string:
        if ch != "0" and ch != ".":
            given += 1
    return given


def run_benchmark_to_csv(
    output_csv_filename,
    file_to_grid,
    grid_to_string,
    recursive_backtracking_solver,
    print_every=25,
    limit=None
):
    fieldnames = [
        "board_index",
        "puzzle_string",
        "given_clues",
        "solution_string_expected",

        "backtracking_solved",
        "backtracking_matches_expected",
        "backtracking_time_ms",
        "backtracking_placements",
        "backtracking_backtracks",

        "norvig_solved",
        "norvig_matches_expected",
        "norvig_time_ms",
        "norvig_assignments",
        "norvig_eliminations",
        "norvig_search_nodes",
        "norvig_contradictions",

        "total_time_ms",

        "skipped_reason"
    ]

    with open(output_csv_filename, mode="w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()

        total = len(boards) if limit is None else min(limit, len(boards))

        for board_index in range(total):
            puzzle_string, solution_string = boards[board_index]

            row = {
                "board_index": board_index,
                "puzzle_string": puzzle_string,
                "given_clues": "",
                "solution_string_expected": solution_string,

                "backtracking_solved": "",
                "backtracking_matches_expected": "",
                "backtracking_time_ms": "",
                "backtracking_placements": "",
                "backtracking_backtracks": "",

                "norvig_solved": "",
                "norvig_matches_expected": "",
                "norvig_time_ms": "",
                "norvig_assignments": "",
                "norvig_eliminations": "",
                "norvig_search_nodes": "",
                "norvig_contradictions": "",

                "total_time_ms": "",

                "skipped_reason": ""
            }

            if not isinstance(puzzle_string, str) or not isinstance(solution_string, str):
                row["skipped_reason"] = "puzzle_or_solution_not_string"
                writer.writerow(row)
                continue

            if len(puzzle_string) != 81:
                row["skipped_reason"] = "puzzle_length_not_81"
                writer.writerow(row)
                continue

            if len(solution_string) != 81:
                row["skipped_reason"] = "solution_length_not_81"
                writer.writerow(row)
                continue

            row["given_clues"] = count_given_clues(puzzle_string)

            backtracking_board = file_to_grid(puzzle_string)
            backtracking_stats = {"placements": 0, "backtracks": 0}

            start_time = time.perf_counter()
            backtracking_solved = recursive_backtracking_solver(
                backtracking_board,
                debug=False,
                stats=backtracking_stats
            )
            backtracking_elapsed_ms = (time.perf_counter() - start_time) * 1000.0

            backtracking_solution_string = grid_to_string(backtracking_board)

            row["backtracking_solved"] = backtracking_solved
            row["backtracking_matches_expected"] = (backtracking_solution_string == solution_string)
            row["backtracking_time_ms"] = backtracking_elapsed_ms
            row["backtracking_placements"] = backtracking_stats["placements"]
            row["backtracking_backtracks"] = backtracking_stats["backtracks"]
            norvig_stats = make_stats()

            start_time = time.perf_counter()
            norvig_solution_string = solve_norvig(puzzle_string, stats=norvig_stats)
            norvig_elapsed_ms = (time.perf_counter() - start_time) * 1000.0

            row["norvig_solved"] = (norvig_solution_string is not None)
            row["norvig_matches_expected"] = (norvig_solution_string == solution_string)
            row["norvig_time_ms"] = norvig_elapsed_ms
            row["norvig_assignments"] = norvig_stats["assignments"]
            row["norvig_eliminations"] = norvig_stats["eliminations"]
            row["norvig_search_nodes"] = norvig_stats["search_nodes"]
            row["norvig_contradictions"] = norvig_stats["contradictions"]
            row["total_time_ms"] = backtracking_elapsed_ms + norvig_elapsed_ms

            writer.writerow(row)

            if print_every is not None and print_every > 0:
                if (board_index + 1) % print_every == 0:
                    print("Processed", board_index + 1, "boards...")

    print("Done. Wrote:", output_csv_filename)