from helpers import *


class Tile:
    def __init__(self, line_raw, index):
        self.line_raw = line_raw
        self.index = index
        self.potential_runs = [[], []]

    def get_state(self):
        return self.line_raw[self.index]

    def set_state(self, state):
        self.line_raw[self.index] = state

    def is_filled(self):
        return self.get_state() == FILLED

    def is_crossed(self):
        return self.get_state() == CROSSED

    def is_unknown(self):
        return self.get_state() == UNKNOWN

    def is_known(self):
        return not self.is_unknown()

    def fill(self):
        self.set_state(FILLED)

    def cross(self):
        self.set_state(CROSSED)

    def add_run(self, potential_run):
        axis_runs = self.potential_runs[potential_run.clue_run.axis]
        axis_runs.append(potential_run)

    def remove_run(self, potential_run):
        axis_runs = self.potential_runs[potential_run.clue_run.axis]
        axis_runs.remove(potential_run)
        if not axis_runs:
            self.cross()