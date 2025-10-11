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

    def __str__(self):
        return f"PotentialRun({potential_run_name(self.clue_run.line_object.axis, self.clue_run.line_object.line_index, self.clue_run.clue_index, self.start, self.end)})"

    def tiles(self):
        return self.clue_run.line_object.line_raw[self.start:self.end]

    def tile_before(self):
        return self.clue_run.line_object.line_raw[self.start - 1] if self.start - 1 >= 0 else None

    def tile_after(self):
        return self.clue_run.line_object.line_raw[self.end] if self.end < len(self.clue_run.line_object.line_raw) else None

    def remove_from_tiles(self):
        for tile in self.tiles():
            tile.remove_run(self)

        dirty_flags = DirtyFlag.NONE

        for tile in self.tiles():
            for axis_runs in tile.potential_runs:
                if not axis_runs:
                    dirty_flags |= tile.cross()
                    break

        return dirty_flags

    # True if the given run of tiles is entirely contained within this one.
    def contains(self, run_start, run_end=None):
        if run_end is None:
            run_end = run_start + 1

        return self.start <= run_start < run_end <= self.end
