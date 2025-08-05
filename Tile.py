from helpers import *

class Tile:
    def __init__(self, line_raw, index):
        self.line_raw = line_raw
        self.index = index
        self.potential_runs = [[], []]

    def get_state(self):
        return self.line_raw[self.index]

    def set_state(self, state):
        if self.is_state(state):
            return False

        assert(self.is_state(State.UNKNOWN))

        self.line_raw[self.index] = state

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
        axis_runs = self.potential_runs[potential_run.clue_run.axis]
        axis_runs.append(potential_run)

    def remove_run(self, potential_run):
        axis_runs = self.potential_runs[potential_run.clue_run.axis]
        axis_runs.remove(potential_run)
        if not axis_runs:
            self.cross()