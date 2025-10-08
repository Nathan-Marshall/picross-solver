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

    def __str__(self):
        return f"ClueRun({clue_run_name(self.axis, self.line_index, self.clue_index)})"

    def remove_run(self, potential_run):
        self.potential_runs.remove(potential_run)
        return DirtyFlag.CLUES | potential_run.remove_from_tiles()

    def remove_first(self):
        first_run = self.potential_runs.pop(0)
        return DirtyFlag.CLUES | first_run.remove_from_tiles()

    def remove_last(self):
        last_run = self.potential_runs.pop()
        return DirtyFlag.CLUES | last_run.remove_from_tiles()

    def assert_valid(self):
        self.solver.assert_puzzle(len(self.potential_runs) > 0, f"{self} has no potential runs.")

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

    # The previous ClueRun's last_end, or the start of the line if this is the first ClueRun
    def prev_end(self):
        if self.prev_run is None:
            return 0
        return self.prev_run.last_end()

    # The next ClueRun's first_start, or the end of the line if this is the last ClueRun
    def next_start(self):
        if self.next_run is None:
            return len(self.line)
        return self.next_run.first_start()

    # True if this is the only ClueRun in the line that can contain the entire given run of indices
    def is_exclusive(self, run_start, run_end=None):
        if run_end is None:
            run_end = run_start + 1

        if not self.is_partially_exclusive_first(run_start, run_end):
            return False

        if not self.is_partially_exclusive_last(run_start, run_end):
            return False

        return True

    # True if this is the first ClueRun in the line that can contain the entire given run of indices
    def is_partially_exclusive_first(self, run_start, run_end=None):
        if run_end is None:
            run_end = run_start + 1

        # Return false if this ClueRun can't contain the run
        if not self.can_contain(run_start, run_end):
            return False

        # Return false if any of the preceding ClueRuns can contain the run
        clue_run = self.prev_run
        while clue_run is not None:
            if clue_run.can_contain(run_start, run_end):
                return False
            clue_run = clue_run.prev_run

        return True

    # True if this is the last ClueRun in the line that can contain the entire given run of indices
    def is_partially_exclusive_last(self, run_start, run_end=None):
        if run_end is None:
            run_end = run_start + 1

        # Return false if this ClueRun can't contain the run
        if not self.can_contain(run_start, run_end):
            return False

        # Return false if any of the following ClueRuns can contain the run
        clue_run = self.next_run
        while clue_run is not None:
            if clue_run.can_contain(run_start, run_end):
                return False
            clue_run = clue_run.next_run

        return True

    # True if there is only one potential run
    def is_fixed(self):
        return len(self.potential_runs) == 1

    def remove_starts_before(self, i):
        if self.first_start() >= i:
            return False

        dirty_flags = DirtyFlag.NONE

        while self.first_start() < i:
            dirty_flags |= self.remove_first()

        dirty_flags |= self.apply()

        return dirty_flags

    def remove_starts_after(self, i):
        if self.last_start() <= i:
            return False

        dirty_flags = DirtyFlag.NONE

        while self.last_start() > i:
            dirty_flags |= self.remove_last()

        dirty_flags |= self.apply()

        return dirty_flags

    def remove_ends_before(self, i):
        if self.first_end() >= i:
            return False

        dirty_flags = DirtyFlag.NONE

        while self.first_end() < i:
            dirty_flags |= self.remove_first()

        dirty_flags |= self.apply()

        return dirty_flags

    def remove_ends_after(self, i):
        if self.last_end() <= i:
            return False

        dirty_flags = DirtyFlag.NONE

        while self.last_end() > i:
            dirty_flags |= self.remove_last()

        dirty_flags |= self.apply()

        return dirty_flags

    def solve_self(self):
        if self.is_fixed():
            return False

        dirty_flags = DirtyFlag.NONE

        for potential_run in self.potential_runs[:]:
            if potential_run not in self.potential_runs:
                continue

            #TODO: Whenever runs are removed, automatically remove any new guaranteed overlaps, rather
            # than checking here.

            # SOLVE SELF 1)
            # Trim guaranteed overlap with adjacent ClueRuns:
            # Remove any start that comes before or adjacent to prev_run.first_end()
            # or any end that comes after or adjacent to next_run.last_start().
            if self.prev_run is not None and potential_run.start <= self.prev_run.first_end():
                dirty_flags |= self.remove_run(potential_run)
                continue
            if self.next_run is not None and potential_run.end >= self.next_run.last_start():
                dirty_flags |= self.remove_run(potential_run)
                continue

        dirty_flags |= self.apply()
        return dirty_flags

    # Apply known tiles to the board
    def apply(self):
        dirty_flags = DirtyFlag.NONE

        # Fill known run
        for i in range(self.last_start(), self.first_end()):
            dirty_flags |= fill(self.line, i)

        # If the run is complete, cross the tile before and the tile after
        if self.is_fixed():
            if self.first_start() > 0:
                dirty_flags |= cross(self.line, self.first_start() - 1)
            if self.last_end() < len(self.line):
                dirty_flags |= cross(self.line, self.last_end())

        return dirty_flags
