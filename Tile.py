import numpy as np
from helpers import *

class Tile:
    def __init__(self, solver, row_index, line_raw, col_index):
        self.solver = solver
        self.row_index = row_index
        self.line_raw = line_raw
        self.col_index = col_index
        self.potential_runs = [[], []]
        self.adjacent_potential_runs = [] # ends just before or starts just after this tile

    def __str__(self):
        return f"Tile(R{self.row_index}, C{self.col_index})"

    def get_state(self):
        return self.line_raw[self.col_index]

    def set_state(self, state):
        if self.is_state(state):
            return False

        # Uncomment and modify this line to display and break on a specific tile
        # self.solver.assert_puzzle(self.row_index != 8 or self.col_index != 18, f"{state_name_verb(state).capitalize()}ing {self}")

        self.solver.assert_puzzle(self.is_unknown(), f"Tried to {state_name_verb(state)} {self} but it's already {state_name(self.get_state())}")

        self.line_raw[self.col_index] = state

        modified_clue_runs = set()

        if state == State.FILLED:
            for adjacent_run in self.adjacent_potential_runs:
                if adjacent_run not in adjacent_run.clue_run.potential_runs:
                    continue
                adjacent_run.clue_run.remove_run(adjacent_run)
                modified_clue_runs.add(adjacent_run.clue_run)
        elif state == State.CROSSED:
            for axis_runs in self.potential_runs:
                for potential_run in axis_runs[:]:
                    if potential_run not in potential_run.clue_run.potential_runs:
                        continue
                    potential_run.clue_run.remove_run(potential_run)
                    modified_clue_runs.add(potential_run.clue_run)
                    self.solver.assert_puzzle(potential_run not in axis_runs, f"Failed to remove potential run {potential_run} from {self}")
            self.solver.assert_puzzle(not self.potential_runs[Axis.ROWS] and not self.potential_runs[Axis.COLS], f"Failed to clear all potential runs from crossed {self}")

        for modified_clue_run in modified_clue_runs:
            modified_clue_run.apply()

        return True

    def is_state(self, state):
        return self.get_state() == state

    def is_filled(self):
        return self.get_state() == State.FILLED

    def is_crossed(self):
        return self.get_state() == State.CROSSED

    def is_unknown(self):
        return self.get_state() == State.UNKNOWN

    def is_known(self):
        return not self.is_unknown()

    def fill(self):
        return self.set_state(State.FILLED)

    def cross(self):
        return self.set_state(State.CROSSED)

    def add_run(self, potential_run):
        axis_runs = self.potential_runs[potential_run.clue_run.line_object.axis]
        axis_runs.append(potential_run)

    def remove_run(self, potential_run):
        axis_runs = self.potential_runs[potential_run.clue_run.line_object.axis]
        axis_runs.remove(potential_run)

    def add_adjacent_run(self, potential_run):
        self.adjacent_potential_runs.append(potential_run)