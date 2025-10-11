from line_profiler_pycharm import profile

from PotentialRun import PotentialRunBase, PotentialRun
from helpers import *

class ClueRunBase:
    def __init__(self):
        pass

    # def __init__(self, other):
    #     self.potential_runs = [PotentialRunBase(potential_run) for potential_run in other.potential_runs]

class ClueRun(ClueRunBase):
    def __init__(self, solver, axis, line_index, clue_index, line, prev_run, length, first_start, last_end):
        super().__init__()

        self.solver = solver
        self.axis = axis
        self.line_index = line_index
        self.clue_index = clue_index
        self.line = line

        self.prev_run = prev_run
        if prev_run is not None:
            prev_run.next_run = self
        self.next_run = None

        self.length = length
        self.potential_runs = [PotentialRun(self, i) for i in range(first_start, last_end - length + 1)]

        for potential_run in self.potential_runs:
            for tile in potential_run.tiles():
                tile.add_run(potential_run)

            tile_before = potential_run.tile_before()
            if tile_before:
                tile_before.add_adjacent_run(potential_run)

            tile_after = potential_run.tile_after()
            if tile_after:
                tile_after.add_adjacent_run(potential_run)

        self.dirty = True # Whether a potential_run was removed since apply() was last called

    def __str__(self):
        return f"ClueRun({clue_run_name(self.axis, self.line_index, self.clue_index)})"

    def remove_run(self, potential_run):
        self.potential_runs.remove(potential_run)
        self.dirty = True
        return DirtyFlag.CLUES | potential_run.remove_from_tiles()

    def remove_first(self):
        first_run = self.potential_runs.pop(0)
        self.dirty = True
        return DirtyFlag.CLUES | first_run.remove_from_tiles()

    def remove_last(self):
        last_run = self.potential_runs.pop()
        self.dirty = True
        return DirtyFlag.CLUES | last_run.remove_from_tiles()

    # Index of the first potential run
    def first_start(self):
        return self.potential_runs[0].start

    # Index past the last tile of the first potential run
    def first_end(self):
        return self.potential_runs[0].end

    # Index of the last potential run
    def last_start(self):
        return self.potential_runs[-1].start

    # Index past the last tile of the last potential run
    def last_end(self):
        return self.potential_runs[-1].end

    # True if any potential run entirely contains the given run
    def can_contain(self, run_start, run_end=None):
        if run_end is None:
            run_end = run_start + 1

        if run_end - run_start > self.length:
            return False

        for potential_run in self.potential_runs:
            if potential_run.start > run_start:
                break

            if run_end <= potential_run.end:
                return True

        return False

    # True if all potential runs entirely contain the given run
    def must_contain(self, run_start, run_end=None):
        if run_end is None:
            run_end = run_start + 1

        for potential_run in self.potential_runs:
            if not potential_run.contains(run_start, run_end):
                return False

        return True

    # Return the subset of this ClueRun's starts for which the resulting run contains the entire given run
    def get_containing_potential_runs(self, run_start, run_end=None):
        if run_end is None:
            run_end = run_start + 1

        return [potential_run for potential_run in self.potential_runs if potential_run.contains(run_start, run_end)]

    # True if there is only one potential run
    def is_fixed(self):
        return len(self.potential_runs) == 1

    def remove_starts_after(self, i):
        dirty_flags = DirtyFlag.NONE

        while self.last_start() > i:
            dirty_flags |= self.remove_last()

        if clues_dirty(dirty_flags):
            dirty_flags |= self.apply()

        return dirty_flags

    def remove_ends_before(self, i):
        dirty_flags = DirtyFlag.NONE

        while self.first_end() < i:
            dirty_flags |= self.remove_first()

        if clues_dirty(dirty_flags):
            dirty_flags |= self.apply()

        return dirty_flags

    def solve_self(self):
        dirty_flags = DirtyFlag.NONE

        if self.is_fixed():
            return dirty_flags

        #TODO: Whenever runs are removed, automatically remove any new guaranteed overlaps, rather
        # than checking here.

        # Trim guaranteed overlap with adjacent ClueRuns:
        # Remove any start that comes before or adjacent to prev_run.first_end()
        # or any end that comes after or adjacent to next_run.last_start().
        if self.prev_run is not None:
            while self.first_start() <= self.prev_run.first_end():
                dirty_flags |= self.remove_first()

        if self.next_run is not None:
            while self.last_end() >= self.next_run.last_start():
                dirty_flags |= self.remove_last()

        if clues_dirty(dirty_flags):
            dirty_flags |= self.apply()

        return dirty_flags

    # Apply known tiles to the board
    def apply(self):
        dirty_flags = DirtyFlag.NONE

        if not self.dirty:
            return dirty_flags

        # Fill known run
        for i in range(self.last_start(), self.first_end()):
            dirty_flags |= fill(self.line, i)

        # If the run is complete, cross the tile before and the tile after
        if self.is_fixed():
            if self.first_start() > 0:
                dirty_flags |= cross(self.line, self.first_start() - 1)
            if self.last_end() < len(self.line):
                dirty_flags |= cross(self.line, self.last_end())

        self.dirty = False
        return dirty_flags
