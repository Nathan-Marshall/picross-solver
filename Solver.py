import numpy as np

from ClueRun import ClueRun
from helpers import *
from picross_display import display_picross


class Solver:
    def __init__(self, puzzle, row_and_col_clues_raw):
        self.puzzle = puzzle
        self.row_and_col_clues_raw = row_and_col_clues_raw
        self.row_and_col_clues = [[], []]

    def get_all_lines(self):
        return [puzzle_line
                for puzzle_view in puzzle_and_transpose(self.puzzle)
                for puzzle_line in puzzle_view]

    def get_all_line_clues(self):
        return [line_clue
                for axis_clues in self.row_and_col_clues
                for line_clue in axis_clues]

    def get_all_clue_runs(self):
        return [clue_run
                for line_clue in self.get_all_line_clues()
                for clue_run in line_clue]

    def get_lines_and_clues(self):
        puzzle_lines = self.get_all_lines()
        line_clues = self.get_all_line_clues()
        return zip(puzzle_lines, line_clues)

    def get_all_line_clues_raw(self):
        return [line_clue_raw
                for axis_clues_raw in self.row_and_col_clues_raw
                for line_clue_raw in axis_clues_raw]

    def get_lines_and_clues_raw(self):
        puzzle_lines = self.get_all_lines()
        line_clues_raw = self.get_all_line_clues_raw()
        return zip(puzzle_lines, line_clues_raw)

    def verify(self):
        return all(self.verify_line(puzzle_line, clue_run_lengths)
                   for puzzle_line, clue_run_lengths in self.get_lines_and_clues_raw())

    @staticmethod
    def verify_line(puzzle_line, clue_run_lengths):
        runs = get_run_starts_ends_lengths(puzzle_line)
        lengths = [length for _, _, length in runs]
        return lengths == clue_run_lengths

    def solve(self, display_steps=False):
        self.initial_solving_pass()

        if display_steps:
            display_picross(self.puzzle, self.row_and_col_clues, block=False)

        puzzle_copy = np.array((0, 0))
        while not np.array_equal(self.puzzle, puzzle_copy) or self.has_dirty_clue_runs():
            puzzle_copy = self.puzzle.copy()
            self.clean_all_clue_runs()
            self.solving_pass()

            if display_steps:
                display_picross(self.puzzle, self.row_and_col_clues, block=False)

    def initial_solving_pass(self):
        for axis, puzzle_view in enumerate(puzzle_and_transpose(self.puzzle)):
            line_clues = self.row_and_col_clues[axis]
            line_clues_raw = self.row_and_col_clues_raw[axis]
            for line_index, puzzle_line in enumerate(puzzle_view):
                clue_run_lengths = line_clues_raw[line_index]
                line_clues.append(self.init_line_clue(clue_run_lengths, puzzle_line))

    @staticmethod
    def init_line_clue(clue_run_lengths, line):
        line_clue = []
        deduction = len(line) - (sum(clue_run_lengths) + len(clue_run_lengths) - 1)

        run_start = 0
        clue_run = None
        for run_length in clue_run_lengths:
            clue_run = ClueRun(line, clue_run, run_length, run_start, run_start + run_length + deduction)
            clue_run.apply()
            line_clue.append(clue_run)
            run_start += run_length + 1

        return line_clue

    def solving_pass(self):
        for puzzle_line, line_clue in self.get_lines_and_clues():
            self.solve_line(puzzle_line, line_clue)

    @staticmethod
    def solve_line(puzzle_line, line_clue):
        for clue_run in line_clue:
            # Any solving logic that does not require other clue runs
            clue_run.solve_self()

        # Cross tiles that are not part of any ClueRuns
        Solver.cross_unclaimed_tiles(puzzle_line, line_clue)

    # If a tile is guaranteed not to be part of any run in the line, cross it out
    @staticmethod
    def cross_unclaimed_tiles(line, line_clue):
        for i in range(len(line)):
            if is_known(line, i):
                continue

            can_contain = False
            for clue_run in line_clue:
                if clue_run.can_contain(i):
                    can_contain = True
                    break

            if not can_contain:
                cross(line, i)

    def has_dirty_clue_runs(self):
        return any(clue_run.dirty
                   for clue_run in self.get_all_clue_runs())

    def clean_all_clue_runs(self):
        for clue_run in self.get_all_clue_runs():
            clue_run.dirty = False
