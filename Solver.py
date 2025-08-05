import numpy as np
from line_profiler_pycharm import profile

from ClueRun import ClueRun
from Tile import Tile
from helpers import *
from picross_display import display_picross

class Solver:
    def __init__(self, puzzle_raw, row_and_col_clues_raw):
        self.puzzle_raw = puzzle_raw
        self.puzzle = Solver.init_tiles(puzzle_raw)
        self.row_and_col_clues_raw = row_and_col_clues_raw
        self.row_and_col_clues = [[], []]

    @staticmethod
    def init_tiles(puzzle_raw):
        puzzle_arr = []
        for line_raw in puzzle_raw:
            line = []
            for i in range(len(line_raw)):
                line.append(Tile(line_raw, i))
            puzzle_arr.append(line)
        return np.array(puzzle_arr, Tile)

    def get_all_lines(self):
        return [puzzle_line
                for puzzle_view in puzzle_and_transpose(self.puzzle)
                for puzzle_line in puzzle_view]

    def enumerate_all_lines(self):
        return [(axis, line_index, puzzle_line)
                for axis, puzzle_view in enumerate(puzzle_and_transpose(self.puzzle))
                for line_index, puzzle_line in enumerate(puzzle_view)]

    def get_all_line_clues(self):
        return [line_clue
                for axis_clues in self.row_and_col_clues
                for line_clue in axis_clues]

    def enumerate_all_line_clues(self):
        return [(axis, line_index, line_clue)
                for axis, axis_clues in enumerate(self.row_and_col_clues)
                for line_index, line_clue in enumerate(axis_clues)]

    def get_all_clue_runs(self):
        return [clue_run
                for line_clue in self.get_all_line_clues()
                for clue_run in line_clue]

    def enumerate_all_clue_runs(self):
        return [(axis, line_index, clue_index, clue_run)
                for axis, line_index, line_clue in self.enumerate_all_line_clues()
                for clue_index, clue_run in enumerate(line_clue)]

    def get_lines_and_clues(self):
        puzzle_lines = self.get_all_lines()
        line_clues = self.get_all_line_clues()
        return zip(puzzle_lines, line_clues)

    def enumerate_lines_and_clues(self):
        enumerated_puzzle_lines = self.enumerate_all_lines()
        line_clues = self.get_all_line_clues()
        return [enumerated_puzzle_line + (line_clue,) for enumerated_puzzle_line, line_clue in zip(enumerated_puzzle_lines, line_clues)]

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

        tiles_changed = True
        while tiles_changed or self.has_dirty_clue_runs():
            self.clean_all_clue_runs()
            tiles_changed = self.solving_pass()

            if display_steps:
                display_picross(self.puzzle_raw, self.row_and_col_clues, block=False)

    def initial_solving_pass(self):
        for axis, puzzle_view in enumerate(puzzle_and_transpose(self.puzzle)):
            line_clues = self.row_and_col_clues[axis]
            line_clues_raw = self.row_and_col_clues_raw[axis]
            for line_index, puzzle_line in enumerate(puzzle_view):
                clue_run_lengths = line_clues_raw[line_index]
                line_clues.append(self.init_line_clue(axis, clue_run_lengths, puzzle_line))

    @staticmethod
    def init_line_clue(axis, clue_run_lengths, line):
        line_clue = []
        deduction = len(line) - (sum(clue_run_lengths) + len(clue_run_lengths) - 1)

        run_start = 0
        clue_run = None
        for run_length in clue_run_lengths:
            clue_run = ClueRun(axis, line, clue_run, run_length, run_start, run_start + run_length + deduction)
            clue_run.apply()
            line_clue.append(clue_run)
            run_start += run_length + 1

        return line_clue

    def solving_pass(self):
        return_val = False

        for puzzle_line, line_clue in self.get_lines_and_clues():
            return_val |= self.solve_line(puzzle_line, line_clue)

        return return_val

    def solve_line(self, puzzle_line, line_clue):
        return_val = False

        for clue_run in enumerate(line_clue):
            # Any solving logic that does not require other clue runs
            return_val |= clue_run.solve_self()

        # Iterate filled runs
        for start, end, length in get_run_starts_ends_lengths(puzzle_line):
            first_containing_clue_run = None
            last_containing_clue_run = None

            guaranteed_run_start = None  # Last start whose resulting run contains this filled run
            guaranteed_run_end = None  # First end whose resulting run contains this filled run
            # If positive, it means all clue runs that can contain this filled run are exactly the length of the
            # guaranteed run
            guaranteed_length = None

            for clue_run in line_clue:
                # Get all starts for which the resulting run contains this filled run
                potential_runs = clue_run.get_containing_potential_runs(start, end)

                if not potential_runs:
                    continue  # Clue run cannot contain this filled run

                for potential_run in potential_runs:
                    # Find last start whose resulting run contains this filled run
                    if guaranteed_run_start is None or guaranteed_run_start < potential_run.start:
                        guaranteed_run_start = potential_run.start

                    # Find first end whose resulting run contains this filled run
                    if guaranteed_run_end is None or guaranteed_run_end > potential_run.end:
                        guaranteed_run_end = potential_run.end

                last_containing_clue_run = clue_run

                if first_containing_clue_run is None:
                    first_containing_clue_run = clue_run

            # Calculate the length of the guaranteed run
            if guaranteed_length is None:
                guaranteed_length = guaranteed_run_end - guaranteed_run_start

            # Set guaranteed_length to -1 if there is a clue run with a larger length that can contain it.
            # -1 indicates that the exact length is not guaranteed.
            for clue_run in line_clue:
                if guaranteed_length != -1 and clue_run.length > guaranteed_length:
                    guaranteed_length = -1
                    break

            if guaranteed_run_start is not None:
                # Fill guaranteed run
                return_val |= fill(puzzle_line, guaranteed_run_start, guaranteed_run_end)

                # If filled run is same length as all runs that can contain it, cross extremities
                if guaranteed_length is not None and guaranteed_length > 0:
                    if guaranteed_run_start > 0:
                        return_val |= cross(puzzle_line, guaranteed_run_start - 1)
                    if guaranteed_run_end < len(puzzle_line):
                        return_val |= cross(puzzle_line, guaranteed_run_end)

            if first_containing_clue_run is None:
                continue

            # TODO: This is way more concise than the partial exclusive logic in solve_self, but that code still
            #  speeds up the algorithm over this
            # The first clue run that can contain this run must not start after the run does.
            n = first_containing_clue_run.last_end() - (start + first_containing_clue_run.length)
            return_val |= first_containing_clue_run.shrink_end(n)

            # The last clue run that can contain this run must not end before the run does.
            n = (end - last_containing_clue_run.length) - last_containing_clue_run.first_start()
            return_val |= last_containing_clue_run.shrink_start(n)

        return return_val

    def has_dirty_clue_runs(self):
        return any(clue_run.dirty
                   for clue_run in self.get_all_clue_runs())

    def clean_all_clue_runs(self):
        for clue_run in self.get_all_clue_runs():
            clue_run.dirty = False