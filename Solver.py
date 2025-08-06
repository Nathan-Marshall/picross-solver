import copy
from collections.abc import Callable
from functools import partial

import numpy as np
from line_profiler_pycharm import profile

import picross_display
from ClueRun import ClueRunBase, ClueRun
from Tile import Tile
from helpers import *
from picross_display import display_picross

class SolverBase:
    def __init__(self):
        pass

    # def __init__(self, other):
    #     self.puzzle_name = other.puzzle_name
    #     self.puzzle_raw = copy.deepcopy(other.puzzle_raw)
    #     self.row_and_col_clues_raw = other.row_and_col_clues_raw
    #     self.row_and_col_clues = [
    #         [
    #             [ClueRunBase(clue_run) for clue_run in line_clue]
    #             for line_clue in axis_clues
    #         ]
    #         for axis_clues in other.row_and_col_clues
    #     ]

# class DebugStackFrame:
#     def __init__(self, title):
#         self.title = title
#         self.modified = False  # True if the board has been modified since this frame's initial state was saved

class Solver(SolverBase):
    def __init__(self, puzzle_name, puzzle_raw, row_and_col_clues_raw, track_changes, display_steps):
        super().__init__()

        self.puzzle_name = puzzle_name
        self.puzzle_raw = puzzle_raw
        self.puzzle = self.init_tiles(puzzle_raw)
        self.row_and_col_clues_raw = row_and_col_clues_raw
        self.row_and_col_clues = [[], []]
        # self.track_changes = track_changes
        self.display_steps = display_steps

        # self.debug_stack = []
        # self.saved_state = None
        # self.saved_state_title = ""

    def assert_puzzle(self, result, message):
        if result:
            return

        # if self.saved_state:
        #     display_picross(self.saved_state, title=self.saved_state_title, block=False)

        display_picross(self, title=f"{self.puzzle_name} assert: {message}")
        print(f"{self.puzzle_name} assert: {message}")

    def init_tiles(self, puzzle_raw):
        puzzle_arr = []
        for line_index, line_raw in enumerate(puzzle_raw):
            line = []
            for i in range(len(line_raw)):
                line.append(Tile(self, line_index, line_raw, i))
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

    def display_changes(self, operation, description_func: Callable[[], str]):
        """
        :param description_func:
            A function that returns a string, because that way we can delay string evaluation until necessary
        """
        tiles_changed = operation()

        if tiles_changed and self.display_steps:
            title = f"{self.puzzle_name} - After {description_func()}"
            display_picross(self, title=title)

            # if self.track_changes:
            #     self.saved_state = SolverBase(self)
            #     self.saved_state_title = title

        return tiles_changed

    @staticmethod
    def verify_line(puzzle_line, clue_run_lengths):
        runs = get_run_starts_ends_lengths(puzzle_line)
        lengths = [length for _, _, length in runs]
        return lengths == clue_run_lengths

    def solve(self):
        self.initialize_clue_runs()
        self.display_changes(self.initial_solving_pass, lambda:"Initial pass")

        tiles_changed = True
        while tiles_changed or self.has_dirty_clue_runs():
            self.clean_all_clue_runs()
            tiles_changed = self.display_changes(self.solving_pass, lambda:"Solving pass")

    def initialize_clue_runs(self):
        for axis, puzzle_view in enumerate(puzzle_and_transpose(self.puzzle)):
            line_clues = self.row_and_col_clues[axis]
            line_clues_raw = self.row_and_col_clues_raw[axis]
            for line_index, puzzle_line in enumerate(puzzle_view):
                clue_run_lengths = line_clues_raw[line_index]
                line_clue = []
                line_clues.append(line_clue)
                self.init_line_clue(line_clue, axis, line_index, clue_run_lengths, puzzle_line)

    def initial_solving_pass(self):
        for clue_run in self.get_all_clue_runs():
            self.display_changes(clue_run.apply, lambda:f"Initialize {clue_run}")

    def init_line_clue(self, line_clue, axis, line_index, clue_run_lengths, line):
        deduction = len(line) - (sum(clue_run_lengths) + len(clue_run_lengths) - 1)

        run_start = 0
        clue_run = None
        for clue_index, run_length in enumerate(clue_run_lengths):
            clue_run = ClueRun(self, axis, line_index, clue_index, line, clue_run, run_length, run_start, run_start + run_length + deduction)
            line_clue.append(clue_run)
            run_start += run_length + 1

        return line_clue

    def solving_pass(self):
        return_val = False

        for axis, line_index, puzzle_line, line_clue in self.enumerate_lines_and_clues():
            return_val |= self.display_changes(partial(self.solve_line, axis, line_index, puzzle_line, line_clue), lambda:f"Solve line {line_name(axis, line_index)}")

        return return_val

    def solve_line(self, axis, line_index, puzzle_line, line_clue):
        return_val = False

        for clue_index, clue_run in enumerate(line_clue):
            # Any solving logic that does not require other clue runs
            return_val |= self.display_changes(clue_run.solve_self, lambda:f"Solve {clue_run}")

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
                return_val |= self.display_changes(partial(fill, puzzle_line, guaranteed_run_start, guaranteed_run_end), lambda:f"Fill guaranteed run {run_name(axis, line_index, guaranteed_run_start, guaranteed_run_end)}")

                # If filled run is same length as all runs that can contain it, cross extremities
                if guaranteed_length is not None and guaranteed_length > 0:
                    if guaranteed_run_start > 0:
                        return_val |= self.display_changes(partial(cross, puzzle_line, guaranteed_run_start - 1), lambda:f"Cross guaranteed start {tile_name(axis, line_index, guaranteed_run_start)}")
                    if guaranteed_run_end < len(puzzle_line):
                        return_val |= self.display_changes(partial(cross, puzzle_line, guaranteed_run_end), lambda:f"Cross guaranteed end {tile_name(axis, line_index, guaranteed_run_end)}")

            if first_containing_clue_run is None:
                continue

            # TODO: This is way more concise than the partial exclusive logic in solve_self, but that code still
            #  speeds up the algorithm over this
            # The first clue run that can contain this run must not start after the run does.
            #return_val |= self.display_changes(partial(first_containing_clue_run.remove_starts_after, start), f"{first_containing_clue_run} first to contain {run_name(axis, line_index, start, end)} so last_start={start}")

            # The last clue run that can contain this run must not end before the run does.
            #return_val |= self.display_changes(partial(last_containing_clue_run.remove_ends_before, end), f"{last_containing_clue_run} last to contain {run_name(axis, line_index, start, end)} so first_end={end}")

        return return_val

    def has_dirty_clue_runs(self):
        return any(clue_run.dirty
                   for clue_run in self.get_all_clue_runs())

    def clean_all_clue_runs(self):
        for clue_run in self.get_all_clue_runs():
            clue_run.dirty = False