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

        if state == State.CROSSED:
            modified_clue_runs = set()

            for axis_runs in self.potential_runs:
                for potential_run in axis_runs[:]:
                    if potential_run not in potential_run.clue_run.potential_runs:
                        continue
                    potential_run.clue_run.remove_run(potential_run)
                    modified_clue_runs.add(potential_run.clue_run)
                    assert(potential_run not in axis_runs)
            assert(not self.potential_runs[Axis.ROWS] and not self.potential_runs[Axis.COLS])

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
        axis_runs = self.potential_runs[potential_run.clue_run.axis]
        axis_runs.append(potential_run)

    def remove_run(self, potential_run):
        axis_runs = self.potential_runs[potential_run.clue_run.axis]
        axis_runs.remove(potential_run)