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
        dirty_flags = operation()

        if board_dirty(dirty_flags) and self.display_steps:
            title = f"{self.puzzle_name} - After {description_func()}"
            display_picross(self, title=title)

            # if self.track_changes:
            #     self.saved_state = SolverBase(self)
            #     self.saved_state_title = title

        return dirty_flags

    @staticmethod
    def verify_line(puzzle_line, clue_run_lengths):
        runs = get_run_starts_ends_lengths(puzzle_line)
        lengths = [length for _, _, length in runs]
        return lengths == clue_run_lengths

    def solve(self):
        dirty_flags = self.initialize_clue_runs()
        dirty_flags |= self.display_changes(self.initial_solving_pass, lambda:"Initial pass")

        while dirty_flags:
            dirty_flags = self.display_changes(self.solving_pass, lambda:"Solving pass")

    def initialize_clue_runs(self):
        for axis, puzzle_view in enumerate(puzzle_and_transpose(self.puzzle)):
            line_clues = self.row_and_col_clues[axis]
            line_clues_raw = self.row_and_col_clues_raw[axis]
            for line_index, puzzle_line in enumerate(puzzle_view):
                clue_run_lengths = line_clues_raw[line_index]
                line_clue = []
                line_clues.append(line_clue)
                self.init_line_clue(line_clue, axis, line_index, clue_run_lengths, puzzle_line)
        return DirtyFlag.CLUES

    def initial_solving_pass(self):
        dirty_flags = DirtyFlag.NONE

        for clue_run in self.get_all_clue_runs():
            dirty_flags |= self.display_changes(clue_run.apply, lambda:f"Initialize {clue_run}")

        return dirty_flags

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
        dirty_flags = DirtyFlag.NONE

        for axis, line_index, puzzle_line, line_clue in self.enumerate_lines_and_clues():
            dirty_flags |= self.display_changes(partial(self.solve_line, axis, line_index, puzzle_line, line_clue), lambda:f"Solve line {line_name(axis, line_index)}")

        return dirty_flags

    def solve_line(self, axis, line_index, puzzle_line, line_clue):
        dirty_flags = DirtyFlag.NONE

        # Trim any guaranteed overlap with the previous or next ClueRun
        for clue_index, clue_run in enumerate(line_clue):
            dirty_flags |= self.display_changes(clue_run.trim_overlap, lambda: f"Solve {clue_run}")

        trimmed_start = [False] * len(line_clue)
        ends_to_trim = [-1] * len(line_clue)

        # Iterate filled runs
        for start, end, length in get_run_starts_ends_lengths(puzzle_line):
            first_containing_clue_run = None
            last_containing_clue_run = None

            first_start = len(puzzle_line)
            last_start = 0
            first_end = len(puzzle_line)
            last_end = 0

            # Iterate all potential runs containing the filled run, from all ClueRuns
            for clue_run in line_clue:
                containing_potential_runs = clue_run.get_containing_potential_runs(start, end)

                if not containing_potential_runs:
                    continue

                if first_containing_clue_run is None:
                    first_containing_clue_run = clue_run
                last_containing_clue_run = clue_run

                for potential_run in containing_potential_runs:
                    first_start = min(first_start, potential_run.start)
                    last_start = max(last_start, potential_run.start)
                    first_end = min(first_end, potential_run.end)
                    last_end = max(last_end, potential_run.end)

            if last_start < start:
                # Fill guaranteed start
                dirty_flags |= self.display_changes(partial(fill, puzzle_line, last_start, start), lambda: f"Fill guaranteed start {run_name(axis, line_index, last_start, start)}")

                if last_start == first_start and first_start > 0:
                    dirty_flags |= self.display_changes(partial(cross, puzzle_line, first_start - 1), lambda: f"Cross before guaranteed start {tile_name(axis, line_index, first_start - 1)}")

            if first_end > end:
                # Fill guaranteed end
                dirty_flags |= self.display_changes(partial(fill, puzzle_line, end, first_end), lambda: f"Fill guaranteed end {run_name(axis, line_index, first_end, end)}")

                if first_end == last_end and last_end < len(puzzle_line):
                    dirty_flags |= self.display_changes(partial(cross, puzzle_line, last_end), lambda: f"Cross after guaranteed end {tile_name(axis, line_index, last_end)}")

            # The first clue run that can contain this run must not start after the run does.
            if not trimmed_start[first_containing_clue_run.clue_index]:
                dirty_flags |= self.display_changes(partial(first_containing_clue_run.remove_starts_after, start), lambda: f"{first_containing_clue_run} first to contain {run_name(axis, line_index, start, end)} so last_start={start}")
                trimmed_start[first_containing_clue_run.clue_index] = True

            # The last clue run that can contain this run must not end before the run does. (mark it for now)
            ends_to_trim[last_containing_clue_run.clue_index] = end

        # Trim any marked ClueRun to the end of the last filled run for which it was the last ClueRun to contain.
        for clue_index, clue_run in enumerate(line_clue):
            if ends_to_trim[clue_index] != -1:
                end = ends_to_trim[clue_index]
                dirty_flags |= self.display_changes(partial(clue_run.remove_ends_before, end), lambda: f"{clue_run} last to contain {run_name(axis, line_index, start, end)} so first_end={end}")

        return dirty_flags
