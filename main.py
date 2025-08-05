import numpy as np
import time

from functools import partial

from picross_display import display_picross
from picross_import import picross_import
from Solver import Solver

all_puzzle_clues = picross_import("puzzles/Large.txt")

def solve_main(i, display, display_steps=False, display_steps_on_callback=False):
    puzzle_clues_raw = all_puzzle_clues[i]
    puzzle_name = f"Puzzle {i}"

    puzzle = np.zeros((len(puzzle_clues_raw[0]), len(puzzle_clues_raw[1])), dtype=int)
    solver = Solver(puzzle_name, puzzle, puzzle_clues_raw, track_changes=display, display_steps=display_steps)

    try:
        solver.solve()
    except Exception as e:
        print(f"{e} occurred in Puzzle {i}")

    if display:
        solve_callback = partial(solve_main, i, display, display_steps=display_steps_on_callback, display_steps_on_callback=display_steps_on_callback)
        display_picross(solver, btn_solve_callback=solve_callback)

    return solver.verify()

def solve_all_main(display_errors, puzzles_to_solve=range(len(all_puzzle_clues))):
    solved_count = 0
    unsolved_count = 0

    time_elapsed = 0

    for i in puzzles_to_solve:
        start_time = time.time()
        solved = solve_main(i, False)
        time_elapsed += time.time() - start_time

        if solved:
            solved_count = solved_count + 1
        else:
            unsolved_count = unsolved_count + 1
            print(f"Failed to solve Puzzle {i}")
            if display_errors:
                print(f"Resolving and displaying Puzzle {i}")
                solve_main(i, True, display_steps_on_callback=True)

    print(f"solved:{solved_count}, unsolved:{unsolved_count}, time:{time_elapsed}")

# solve_all_main(True, range(30))
solve_all_main(False)
# solve_main(16, True)