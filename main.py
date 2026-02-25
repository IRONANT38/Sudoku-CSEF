import random
import time
from board import boards
from norvig_solver import solve_norvig, make_stats
from benchmark_runner import run_benchmark_to_csv
from classify_boards import classify_boards

easy = (
    "004300209005009001070060043006002087190007400050083000600000105003508690042910300",
    "864371259325849761971265843436192587198657432257483916689734125713528694542916378"
)
def file_to_grid(data):
    """
    Turns an 81-character string like '0043...' into a 9x9 grid of integers.
    0 means "empty".
    IMPORTANT: This project uses board[row_index][column_index] everywhere.
    """
    grid = []
    for row_index in range(9):
        current_row = []
        for column_index in range(9):
            index = row_index * 9 + column_index
            current_row.append(int(data[index]))
        grid.append(current_row)
    return grid
def grid_to_string(board):
    """
    Turns a 9x9 grid back into an 81-character string.
    """
    output = ""
    for row_index in range(9):
        for column_index in range(9):
            output += str(board[row_index][column_index])
    return output
def print_board(board):
    """
    Prints the board with nice 3x3 separators.
    """
    for row_index in range(9):
        if row_index % 3 == 0 and row_index != 0:
            print("---------------------")

        row_text_parts = []
        for column_index in range(9):
            if column_index % 3 == 0 and column_index != 0:
                row_text_parts.append("|")

            value = board[row_index][column_index]
            if value == 0:
                row_text_parts.append(".")
            else:
                row_text_parts.append(str(value))

        print(" ".join(row_text_parts))
def get_row_values(board, row_index):
    """
    Returns a list of the 9 values in a row.
    """
    values = []
    for column_index in range(9):
        values.append(board[row_index][column_index])
    return values

def get_column_values(board, column_index):
    """
    Returns a list of the 9 values in a column.
    """
    values = []
    for row_index in range(9):
        values.append(board[row_index][column_index])
    return values
def get_box_values(board, row_index, column_index):
    """
    Returns a list of the 9 values in the 3x3 box that contains (row_index, column_index).
    """
    box_start_row = (row_index // 3) * 3
    box_start_column = (column_index // 3) * 3

    values = []
    for r in range(box_start_row, box_start_row + 3):
        for c in range(box_start_column, box_start_column + 3):
            values.append(board[r][c])

    return values
def count_conflicts(board):
    conflicts = 0

    for row_index in range(9):
        for column_index in range(9):
            value = board[row_index][column_index]
            if value == 0:
                continue
            row_has_duplicate = False
            for other_column_index in range(9):
                if other_column_index == column_index:
                    continue
                if board[row_index][other_column_index] == value:
                    row_has_duplicate = True
                    break

            if row_has_duplicate:
                conflicts += 1
                continue

            column_has_duplicate = False
            for other_row_index in range(9):
                if other_row_index == row_index:
                    continue
                if board[other_row_index][column_index] == value:
                    column_has_duplicate = True
                    break

            if column_has_duplicate:
                conflicts += 1
                continue

            box_start_row = (row_index // 3) * 3
            box_start_column = (column_index // 3) * 3

            box_has_duplicate = False
            for other_row_index in range(box_start_row, box_start_row + 3):
                for other_column_index in range(box_start_column, box_start_column + 3):
                    if other_row_index == row_index and other_column_index == column_index:
                        continue
                    if board[other_row_index][other_column_index] == value:
                        box_has_duplicate = True
                        break
                if box_has_duplicate:
                    break

            if box_has_duplicate:
                conflicts += 1
                continue

    return conflicts
    
def find_empty_cell(board):
    for row_index in range(9):
        for col_index in range(9):
            if board[row_index][col_index] == 0:
                return (row_index, col_index)
    return None

def is_valid_placement(board, row_index, column_index, candidate_number):
    if candidate_number in get_row_values(board, row_index):
        return False
    if candidate_number in get_column_values(board, column_index):
        return False
    if candidate_number in get_box_values(board, row_index, column_index):
        return False
    return True
    
def shuffle_solver(board):
    for col in range(9):
        numbers_to_place = [1,2,3,4,5,6,7,8,9]
        for row in range(9):
            if puzzle[row][col] != 0:
                val = puzzle[row][col]
                if val in numbers_to_place:
                    numbers_to_place.remove(val)

        random.shuffle(numbers_to_place)
        fill_index = 0
        for row in range(9):
            if puzzle[row][col] == 0:
                board[row][col] = numbers_to_place[fill_index]
                fill_index += 1
                
def shuffle_solver_with_constraints(board):
    for row in range(9):
        numbers_to_place = list(range(1, 10))
        for col in range(9):
            val = board[row][col]
            if val != 0 and val in numbers_to_place:
                numbers_to_place.remove(val)
        random.shuffle(numbers_to_place)
        for col in range(9):
            if board[row][col] != 0:
                continue
            placed = False
            for i in range(len(numbers_to_place)):
                candidate = numbers_to_place[0]
                if candidate not in get_column_values(board, col) and candidate not in get_box_values(board, row, col):
                    board[row][col] = candidate
                    numbers_to_place.pop(0)  
                    placed = True
                    break
                else:
                    numbers_to_place.append(numbers_to_place.pop(0))
            if not placed:
                board[row][col] = 0         

def recursive_backtracking_solver(board, debug=False, depth=0, stats=None):
    if stats is None:
        stats = {"placements": 0, "backtracks": 0}
    empty_cell = find_empty_cell(board)
    if empty_cell == None:
        return True 
    row_index, column_index = empty_cell

    candidate_numbers = [1,2,3,4,5,6,7,8,9]
    for candidate_number in candidate_numbers:
        if is_valid_placement(board, row_index, column_index, candidate_number):
            board[row_index][column_index] = candidate_number
            stats["placements"]+= 1

            if debug:
                    indent = "  " * depth
                    print(indent + "Place", candidate_number, "at", (row_index, column_index))
            
            if recursive_backtracking_solver(board, debug=debug, depth=depth+1, stats=stats):
                return True
            board[row_index][column_index] = 0
            stats["backtracks"] +=1

            if debug:
                indent = "  " * depth
                print(indent + "Backtrack at", (row_index, column_index))
    return False
        


 
puzzle_string, solution_string = easy
board = file_to_grid(puzzle_string)
puzzle = file_to_grid(puzzle_string)

print("Original Puzzle:\n")
print_board(board)

print("\nBoard after shuffle pass:\n")
shuffle_solver(board)
print_board(board)

print("\nBoard after shuffle constraints pass:\n")
board = file_to_grid(puzzle_string)
shuffle_solver_with_constraints(board)
print_board(board)

print("\nBoard with recursive backtracking:\n")
board = file_to_grid(puzzle_string)
stats = {"placements": 0, "backtracks": 0}

start_time = time.perf_counter()
solved = recursive_backtracking_solver(board, debug=False, stats=stats)
elapsed_seconds = time.perf_counter() - start_time
print_board(board)
print("\nBacktracking time (milliseconds):", elapsed_seconds*1000)
print("Placements:", stats["placements"], "Backtracks:", stats["backtracks"])
print("Matches known solution:", grid_to_string(board) == solution_string)

print("\nNorvig solver result:\n")
norvig_stats = make_stats()
start_time = time.perf_counter()
norvig_solution_string = solve_norvig(puzzle_string, stats=norvig_stats)
elapsed_seconds = time.perf_counter() - start_time
print("\nNorvig matches known solution:", norvig_solution_string == solution_string)
print("Norvig time (milliseconds):",  elapsed_seconds*1000)
print("Assignments:", norvig_stats["assignments"])
print("Eliminations:", norvig_stats["eliminations"])
print("Search nodes:", norvig_stats["search_nodes"])
print("Contradictions:", norvig_stats["contradictions"])

run_benchmark_to_csv(
    output_csv_filename="benchmark_results.csv",
    file_to_grid=file_to_grid,
    grid_to_string=grid_to_string,
    recursive_backtracking_solver=recursive_backtracking_solver,
    print_every=25,
    limit=None
)
classify_boards(
    input_csv="benchmark_results.csv",
    output_py="classified_boards.py"
)