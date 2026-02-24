import tkinter as tk
from tkinter import font, Checkbutton, IntVar, messagebox
import board as game_data
import random

root = tk.Tk()
root.title("Sudoku - Easy")
root.config(bg="#444444")
root.tk.call("tk", "scaling",0.5)

entry_widgets = {}

ERROR_BG = "#ffb3b3"
CORRECT_BG = "#b3ffb3"
ARMY_BG = "#768900"
GREY_BG = "#999999"
WHITE_BG = "#FFFFFF"
BLACK_BG = "#000000"
HINT_BG = "#b3ff66"
NOTE_FG = "#2E86C1"

HILITE_UNIT_BG = "#d9e8ff"
HILITE_SEL_BG = "#8fb6ff"
HILITE_SAME_BG = "#bcd4ff"

board = []
solution = []
current_mode = "easy"
last_hint = None

board_font = font.Font(family="Helvetica", size=26, weight="bold")
user_font = font.Font(family="Helvetica", size=26, weight="bold")
note_font = font.Font(family="Helvetica", size=22, weight="bold")

subscript_map = [
    "\u2080", "\u2081", "\u2082", "\u2083", "\u2084",
    "\u2085", "\u2086", "\u2087", "\u2088", "\u2089"
]
SUBS_SET = set(subscript_map[1:])
DIGITS = set("123456789")

def has_subscripts(text):
    return any(character in SUBS_SET for character in text)

def normalize_notes(text):
    digits = set()
    for character in text:
        if character in DIGITS:
            digits.add(int(character))
        elif character in SUBS_SET:
            digits.add(subscript_map.index(character))
    return "".join(subscript_map[d] for d in sorted(digits))

def file_to_grid(data):
    return [[int(data[row * 9 + col]) for col in range(9)] for row in range(9)]

def remove_note(cell, digit):
    if cell is None or cell.cget("state") == "readonly":
        return

    txt = cell.get()
    sub_to_remove = subscript_map[digit]

    if sub_to_remove in txt:
        new_txt = "".join([character for character in txt if character != sub_to_remove])
        old_val = cell.cget("validate")
        cell.config(validate="none")
        cell.delete(0, tk.END)
        cell.insert(0, new_txt)
        cell.config(validate=old_val)
        refresh_cell(cell)

def refresh_cell(cell):
    if cell is None or cell.cget("state") == "readonly":
        return

    txt = cell.get().strip()

    if len(txt) == 1 and txt in DIGITS:
        cell.config(font=board_font, fg=BLACK_BG)
    elif has_subscripts(txt):
        cell.config(font=note_font, fg=NOTE_FG)
    else:
        cell.config(font=board_font, fg=BLACK_BG)

def eliminate_notes(row, col, digit):
    for i in range(9):
        remove_note(entry_widgets.get((row, i)), digit)
        remove_note(entry_widgets.get((i, col)), digit)

    br = (row // 3) * 3
    bc = (col // 3) * 3
    for rr in range(br, br + 3):
        for cc in range(bc, bc + 3):
            remove_note(entry_widgets.get((rr, cc)), digit)

def on_focus_in(event):
    focused_widget = event.widget
    focused_widget.selection_range(0, tk.END)
    focused_widget.icursor(tk.END)

    target_row_index = focused_widget.row
    target_column_index = focused_widget.column
    current_cell_text = focused_widget.get().strip()
    
    target_value_to_match = None
    if current_cell_text in DIGITS:
        if len(current_cell_text) == 1:
            target_value_to_match = int(current_cell_text)

    box_start_row = (target_row_index // 3) * 3
    box_start_column = (target_column_index // 3) * 3

    for (current_row, current_column), cell in entry_widgets.items():
        background_attribute = ""
        default_color = ""

        if cell.cget("state") == "readonly":
            background_attribute = "readonlybackground"
            default_color = GREY_BG
        else:
            background_attribute = "bg"
            default_color = WHITE_BG

        is_in_same_row = (current_row == target_row_index)
        is_in_same_column = (current_column == target_column_index)
        
        is_in_same_box = False
        if box_start_row <= current_row < box_start_row + 3:
            if box_start_column <= current_column < box_start_column + 3:
                is_in_same_box = True

        is_matching_number = False
        cell_contents = cell.get().strip()
        if target_value_to_match is not None:
            if cell_contents in DIGITS:
                if len(cell_contents) == 1:
                    if int(cell_contents) == target_value_to_match:
                        is_matching_number = True

        if is_matching_number:
            cell.config({background_attribute: HILITE_SAME_BG})
        elif is_in_same_row or is_in_same_column or is_in_same_box:
            cell.config({background_attribute: HILITE_UNIT_BG})
        else:
            cell.config({background_attribute: default_color})

    if focused_widget.cget("state") == "readonly":
        focused_widget.config(readonlybackground=HILITE_SEL_BG)
    else:
        focused_widget.config(bg=HILITE_SEL_BG)

def pick_dataset(difficulty_mode):
    if hasattr(game_data, difficulty_mode):
        found_data = getattr(game_data, difficulty_mode)
        if isinstance(found_data, list):
            if len(found_data) > 0:
                return found_data

    difficulty_data_name = difficulty_mode + "_data"
    if hasattr(game_data, difficulty_data_name):
        found_data = getattr(game_data, difficulty_data_name)
        if isinstance(found_data, list):
            if len(found_data) > 0:
                return found_data

    if difficulty_mode == "demon":
        if hasattr(game_data, "hard"):
            return game_data.hard

    return game_data.easy

def set_mode_controls():
    demon = (current_mode == "demon")
    state = "disabled" if demon else "normal"

    notes_btn.config(state=state)
    check_btn.config(state=state)
    hint_btn.config(state=state)

    if demon:
        notes_var.set(0)
        apply_notes_mode()

def load_game(mode):
    global board, solution, current_mode, last_hint
    current_mode = mode
    last_hint = None
    root.title(f"Sudoku - {mode.title()}")
    dataset = pick_dataset(mode)
    puzzle, sol = random.choice(dataset)
    board_grid = file_to_grid(puzzle)
    sol_grid = file_to_grid(sol)
    board[:] = board_grid
    solution[:] = sol_grid
    draw_board()
    set_mode_controls()
    root.update_idletasks()
    root.update()

def check_victory():
    for row in range(9):
        for col in range(9):
            if board[row][col] != solution[row][col]:
                return False
    for cell in entry_widgets.values():
        cell.config(readonlybackground=CORRECT_BG, bg=CORRECT_BG)
        cell.config(state="readonly")

    messagebox.showinfo("Success", "You Win!")
    return True

def is_valid_unit(value, widget_name):
    widget = root.nametowidget(widget_name)
    row, col = widget.row, widget.column

    if value == "":
        board[row][col] = 0
        widget.config(bg=WHITE_BG)
        refresh_cell(widget)
        return True

    if len(value) >= 1:
        last_character_typed = value[-1]
        if last_character_typed in DIGITS:
            val = int(last_character_typed)
            board[row][col] = val
            widget.config(bg=WHITE_BG)
            
            if len(value) > 1:
                root.after_idle(lambda: widget.delete(0, tk.END))
                root.after_idle(lambda: widget.insert(0, last_character_typed))
                root.after_idle(lambda: refresh_cell(widget))

            eliminate_notes(row, col, val)
            refresh_cell(widget)
            check_victory()
            return True

    return False

check_cmd = (root.register(is_valid_unit), "%P", "%W")

draw_border = tk.Frame(root, bg=ARMY_BG, bd=3, relief="solid")
draw_border.pack()

inner_frame = tk.Frame(draw_border, bg=ARMY_BG)
inner_frame.pack(padx=8, pady=8)

def on_key_notes(event, cell_widget):
    if not notes_var.get():
        return

    if event.keysym in ("BackSpace", "Delete"):
        cell_widget.delete(0, tk.END)
        refresh_cell(cell_widget)
        return "break"

    if event.char in DIGITS:
        d = int(event.char)
        sub = subscript_map[d]
        txt = cell_widget.get()
        txt = txt.replace(sub, "") if sub in txt else txt + sub
        cell_widget.delete(0, tk.END)
        cell_widget.insert(0, normalize_notes(txt))
        refresh_cell(cell_widget)
        return "break"
    return "break"

def apply_notes_mode():
    notes_on = bool(notes_var.get())
    for (row, col), cell in entry_widgets.items():
        if cell.cget("state") == "readonly":
            continue

        if notes_on:
            cell.config(validate="none")
            cell.bind("<KeyPress>", lambda e, cc=cell: on_key_notes(e, cc))
            refresh_cell(cell)
        else:
            cell.unbind("<KeyPress>")
            cell.config(validate="key", validatecommand=check_cmd)
            refresh_cell(cell)

def draw_board():
    for w in inner_frame.winfo_children():
        w.destroy()
    entry_widgets.clear()

    for br in range(3):
        for bc in range(3):
            box = tk.Frame(inner_frame, bd=2, relief="solid", bg=ARMY_BG)
            box.grid(row=br, column=bc, padx=4, pady=4)

            for row in range(3):
                for col in range(3):
                    rr = br * 3 + row
                    cc = bc * 3 + col
                    cell = tk.Entry(
                        box,
                        width=4,
                        bg=WHITE_BG,
                        fg=BLACK_BG,
                        justify="center",
                        validate="none"
                    )
                    cell.row, cell.column = rr, cc
                    cell.grid(row=row, column=col, ipadx=6, ipady=16, padx=1, pady=1)
                    entry_widgets[(rr, cc)] = cell

                    if board[rr][cc] != 0:
                        cell.insert(0, str(board[rr][cc]))
                        cell.config(
                            state="readonly",
                            font=user_font,
                            fg=BLACK_BG,
                            readonlybackground=GREY_BG
                        )
                        cell.bind("<Button-1>", on_focus_in) #left mouse
                    else:
                        cell.config(font=board_font, fg=BLACK_BG)
                        cell.bind("<FocusIn>", on_focus_in)
                        refresh_cell(cell)

    apply_notes_mode()

def check_board():
    for (row, col), cell in entry_widgets.items():
        if cell.cget("state") == "readonly":
            continue
        txt = cell.get().strip()

        if txt == "" or has_subscripts(txt) or not txt.isdigit():
            cell.config(bg=WHITE_BG)
            continue

        cell.config(bg=CORRECT_BG if int(txt) == solution[row][col] else ERROR_BG)

def flash(cell, count=6):
    if count <= 0:
        cell.config(bg=HINT_BG)
        return
    cell.config(bg=WHITE_BG if count % 2 == 0 else HINT_BG)
    root.after(120, lambda: flash(cell, count - 1))

def hint():
    global last_hint

    if last_hint is not None:
        pr, pc = last_hint
        prev = entry_widgets.get((pr, pc))
        if prev and prev.cget("state") != "readonly":
            prev.config(bg=WHITE_BG)
        last_hint = None

    candidates = []
    for (row, col), cell in entry_widgets.items():
        if cell.cget("state") == "readonly":
            continue
        txt = cell.get().strip()
        if txt == "" or has_subscripts(txt) or (txt.isdigit() and int(txt) != solution[row][col]):
            candidates.append((row, col))

    if not candidates:
        messagebox.showinfo("Hint", "No hint available.")
        return

    row, col = random.choice(candidates)
    cell = entry_widgets[(row, col)]

    if notes_var.get():
        notes_var.set(0)
        apply_notes_mode()

    cell.delete(0, tk.END)
    cell.insert(0, str(solution[row][col]))
    board[row][col] = solution[row][col]

    eliminate_notes(row, col, solution[row][col])

    cell.config(bg=HINT_BG)
    last_hint = (row, col)

    flash(cell)

    messagebox.showinfo("Hint", f"Filled: Row {row+1}, Column {col+1} = {solution[row][col]}")

def clear_game():
    load_game(current_mode)

btn_bar = tk.Frame(root, bg=GREY_BG)
btn_bar.pack(pady=10)

notes_var = IntVar(value=0)
notes_btn = Checkbutton(btn_bar, text="Notes", variable=notes_var, command=apply_notes_mode)
notes_btn.grid(row=0, column=0, padx=6, pady=6)

check_btn = tk.Button(btn_bar, text="Check", command=check_board)
check_btn.grid(row=0, column=1, padx=6, pady=6)

hint_btn = tk.Button(btn_bar, text="Hint", command=hint)
hint_btn.grid(row=0, column=2, padx=6, pady=6)

tk.Button(btn_bar, text="Clear", command=clear_game).grid(row=0, column=3, padx=6, pady=6)

tk.Button(btn_bar, text="Easy", command=lambda: load_game("easy")).grid(row=1, column=0, padx=6, pady=6)
tk.Button(btn_bar, text="Medium", command=lambda: load_game("medium")).grid(row=1, column=1, padx=6, pady=6)
tk.Button(btn_bar, text="Hard", command=lambda: load_game("hard")).grid(row=1, column=2, padx=6, pady=6)
tk.Button(btn_bar, text="Demon", command=lambda: load_game("demon")).grid(row=1, column=3, padx=6, pady=6)

load_game("easy")
root.mainloop()