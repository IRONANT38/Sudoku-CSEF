# Mr.Sudoku
## Abstract
The purpose of this project was to design and test my own Sudoku-solving algorithm and compare its speed and accuracy to a basic backtracking method and Peter Norvig’s Sudoku solver, which uses constraint propagation combined with search. I also created a full Sudoku game with a graphical user interface and used the solvers to sort puzzles by difficulty, allowing players to access a wide range of boards.
To investigate performance on puzzles of varying difficulty levels, I first tested each solver on 200 Sudoku puzzles collected from books, websites, and manually created puzzles to verify correctness and establish a baseline. After confirming the code functioned properly, I tested the solvers on a dataset of one million Sudoku puzzles and solutions. I also ran additional benchmarks on a smaller controlled test set to measure detailed performance. Difficulty was estimated by the number of empty cells, since puzzles with fewer starting clues are generally harder. For each puzzle, I recorded whether the solver found the correct solution and how long it took to solve.
My results showed that Norvig’s solver was the fastest and most reliable on puzzles with many empty cells, while my algorithm performed best on easier puzzles with fewer empty cells because it relied mainly on logical deductions and needed less guessing. The basic backtracking method was usually slower than Norvig’s, especially on harder puzzles where constraint propagation reduced the search space.
In conclusion, different algorithms perform better depending on puzzle difficulty. Simpler logical strategies are effective for easier boards, while more advanced techniques are needed for harder ones.

## Results
While both algorithms solved 100% of the puzzles, they diverged significantly in efficiency as the search space expanded. My custom algorithm relied on logical deductions that matched human-play styles, resulting in sub-millisecond solving times for boards with more than 33 clues. Norvig’s solver utilized constraint propagation to eliminate candidates before searching, preventing the exponential 'backtrack explosion' seen in my custom solver at 25 clues. In conclusion, different algorithms perform better depending on puzzle difficulty. Simpler logical strategies (like mine) are effective for easier boards, while more advanced techniques (like Norvig’s solution) are needed to quickly solve harder ones.

**===== FINAL BENCHMARK DATA =====**<br>
**Total Boards Tested:** 1,000,000<br>
**Custom Solver Max Time:** 221.65 ms<br> 
**Norvig Solver Max Time:** 27.00 ms<br>
**Custom Solver Mean (Overall):** 2.29 ms<br>
**Norvig Solver Mean (Overall):** 2.19 ms<br>



# What comes next
### Sharing the source code
⬇️ [Download and run the Python code](https://github.com/IRONANT38/Sudoku-CSEF/archive/refs/heads/main.zip) ⬇️
### Bringing it online
I used AI to recreate my Python code and translate it into JavaScript to make my work more easily accessible online.  
You can find it here:  
🔗 [Mr.Sudoku](https://IRONANT38.github.io//Sudoku-CSEF) 🔗
