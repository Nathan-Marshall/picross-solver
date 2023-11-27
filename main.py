import numpy as np

from picross_display import display_picross, block_until_windows_closed
from picross_import import picross_import
from picross_solver import solve


all_puzzle_clues = picross_import('puzzles/Large.txt')
puzzle_clues_raw = all_puzzle_clues[0]

puzzle = np.zeros((len(puzzle_clues_raw[0]), len(puzzle_clues_raw[1])), dtype=int)
row_and_col_clues = [[], []]


def solve_main():
    solve(puzzle, row_and_col_clues, puzzle_clues_raw)


solve_main()
display_picross(puzzle, row_and_col_clues, btn_solve_callback=solve_main)
