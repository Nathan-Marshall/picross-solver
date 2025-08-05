from helpers import *

class PotentialRunBase:
    def __init__(self):
        pass

    # def __init__(self, other):
    #     self.start = other.start
    #     self.end = other.end

class PotentialRun(PotentialRunBase):
    def __init__(self, clue_run, start):
        super().__init__()

        self.clue_run = clue_run
        self.start = start
        self.end = start + clue_run.length

    def tiles(self):
        return self.clue_run.line[self.start:self.end]

    def remove_from_tiles(self):
        for tile in self.tiles():
            tile.remove_run(self)

        return_val = False

        for tile in self.tiles():
            for axis_runs in tile.potential_runs:
                if not axis_runs:
                    return_val |= tile.cross()
                    break

        return return_val

    # True if the given run of tiles is entirely contained within this one.
    def contains(self, run_start, run_end=None):
        if run_end is None:
            run_end = run_start + 1

        return self.start <= run_start < run_end <= self.end

    def contains_cross(self):
        for tile in self.tiles():
            if tile.is_crossed():
                return True
        return False

    def next_to_filled(self):
        if self.start > 0 and self.clue_run.line[self.start - 1].is_filled():
            return True

        if self.end < len(self.clue_run.line) and self.clue_run.line[self.end].is_filled():
            return True

        return False