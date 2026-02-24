import csv


def classify_boards(
    input_csv="benchmark_results.csv",
    output_py="classified_boards.py"
):
    rows = []

    with open(input_csv, mode="r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            puzzle = row.get("puzzle_string", "")
            solution = row.get("solution_string_expected", "")
            total_time = row.get("total_time_ms", "")

            if (
                isinstance(puzzle, str) and len(puzzle) == 81 and
                isinstance(solution, str) and len(solution) == 81
            ):
                try:
                    total_time = float(total_time)
                    rows.append((total_time, puzzle, solution))
                except:
                    pass

    rows.sort(key=lambda x: x[0])

    n = len(rows)
    cut1 = n // 3
    cut2 = (2 * n) // 3

    easy = rows[:cut1]
    medium = rows[cut1:cut2]
    hard = rows[cut2:]

    with open(output_py, "w", encoding="utf-8") as f:
        f.write("easy = [\n")
        for _, puzzle, solution in easy:
            f.write(f"    ({repr(puzzle)}, {repr(solution)}),\n")
        f.write("]\n\n")

        f.write("medium = [\n")
        for _, puzzle, solution in medium:
            f.write(f"    ({repr(puzzle)}, {repr(solution)}),\n")
        f.write("]\n\n")

        f.write("hard = [\n")
        for _, puzzle, solution in hard:
            f.write(f"    ({repr(puzzle)}, {repr(solution)}),\n")
        f.write("]\n")


if __name__ == "__main__":
    classify_boards()