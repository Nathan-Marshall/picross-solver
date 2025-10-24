import copy
from collections.abc import Callable

import numpy as np
from line_profiler_pycharm import profile

from Line import Line
from Tile import Tile
from helpers import *
from picross_display import display_picross

class Solver:
    def __init__(self, puzzle_name, puzzle_raw, row_and_col_clues_raw, display_steps):
        self.puzzle_name = puzzle_name
        self.puzzle_raw = puzzle_raw
        self.puzzle = self.init_tiles(puzzle_raw)
        self.row_and_col_clues_raw = row_and_col_clues_raw
        self.line_objects = [[], []]
        self.display_steps = display_steps

    def assert_puzzle(self, result, message):
        if result:
            return

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

    def get_all_puzzle_lines(self):
        return [puzzle_line
                for puzzle_view in puzzle_and_transpose(self.puzzle)
                for puzzle_line in puzzle_view]

    def get_all_line_objects(self):
        return [line_object
                for axis_lines in self.line_objects
                for line_object in axis_lines]

    def get_all_clue_runs(self):
        return [clue_run
                for line_clue in self.get_all_line_objects()
                for clue_run in line_clue.clue_runs]

    def get_all_line_clues_raw(self):
        return [line_clue_raw
                for axis_clues_raw in self.row_and_col_clues_raw
                for line_clue_raw in axis_clues_raw]

    def verify(self):
        return all(line_object.verify() for line_object in self.get_all_line_objects())

    def display_changes(self, operation, description_func: Callable[[], str]):
        """
        :param description_func:
            A function that returns a string, because that way we can delay string evaluation until necessary
        """
        dirty_flags = operation()

        if board_dirty(dirty_flags) and self.display_steps:
            title = f"{self.puzzle_name} - After {description_func()}"
            display_picross(self, title=title)

        return dirty_flags

    def solve(self):
        dirty_flags = self.initialize_clue_runs()
        dirty_flags |= self.display_changes(self.initial_solving_pass, lambda:"Initial pass")

        while dirty_flags:
            dirty_flags = self.display_changes(self.solving_pass, lambda:"Solving pass")

    def initialize_clue_runs(self):
        for axis, puzzle_view in enumerate(puzzle_and_transpose(self.puzzle)):
            axis_lines = self.line_objects[axis]
            line_clues_raw = self.row_and_col_clues_raw[axis]
            for line_index, puzzle_line in enumerate(puzzle_view):
                clue_run_lengths = line_clues_raw[line_index]
                line_object = Line(self, axis, line_index, clue_run_lengths, puzzle_line)
                axis_lines.append(line_object)
        return DirtyFlag.CLUES

    def initial_solving_pass(self):
        dirty_flags = DirtyFlag.NONE

        for clue_run in self.get_all_clue_runs():
            dirty_flags |= self.display_changes(clue_run.apply, lambda:f"Initialize {clue_run}")

        return dirty_flags

    def solving_pass(self):
        dirty_flags = DirtyFlag.NONE

        for line_object in self.get_all_line_objects():
            dirty_flags |= self.display_changes(line_object.solve_line, lambda:f"Solve line {line_name(line_object.axis, line_object.line_index)}")

        return dirty_flags
