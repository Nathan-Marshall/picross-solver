import numpy as np
import time

from functools import partial

from picross_display import display_picross, block_until_windows_closed
from picross_import import picross_import
from picross_solver import solve
from picross_solver import verify


all_puzzle_clues = picross_import('puzzles/Large.txt')


def solve_main(i, display, display_steps=False):
    puzzle_clues_raw = all_puzzle_clues[i]

    puzzle = np.zeros((len(puzzle_clues_raw[0]), len(puzzle_clues_raw[1])), dtype=int)
    row_and_col_clues = [[], []]
    solve(puzzle, row_and_col_clues, puzzle_clues_raw, display_steps=display_steps)

    if display:
        puzzle_name = 'Puzzle ' + str(i)
        solve_callback = partial(solve_main, i, display, display_steps=display_steps)
        display_picross(puzzle, row_and_col_clues, name=puzzle_name, btn_solve_callback=solve_callback)

    return verify(puzzle, puzzle_clues_raw)


def solve_all_main(display_errors):
    solved_count = 0
    unsolved_count = 0

    time_elapsed = 0

    for i in range(len(all_puzzle_clues)):
        start_time = time.time()
        solved = solve_main(i, False)
        time_elapsed += time.time() - start_time

        if solved:
            solved_count = solved_count + 1
        else:
            unsolved_count = unsolved_count + 1
            if display_errors:
                solve_main(i, True)

    print('solved:' + str(solved_count) + ', unsolved:' + str(unsolved_count) + ', time:' + str(time_elapsed))


solve_all_main(False)
# solve_main(16, True)
