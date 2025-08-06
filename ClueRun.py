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

        self.dirty = False  # cleared every pass; if true, indicates that the run was modified this pass

    def __str__(self):
        return f"ClueRun({clue_run_name(self.axis, self.line_index, self.clue_index)})"

    def remove_run(self, potential_run):
        self.potential_runs.remove(potential_run)
        self.dirty = True
        return potential_run.remove_from_tiles()

    def remove_first(self):
        first_run = self.potential_runs.pop(0)
        self.dirty = True
        return first_run.remove_from_tiles()

    def remove_last(self):
        last_run = self.potential_runs.pop()
        self.dirty = True
        return last_run.remove_from_tiles()

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

    def remove_starts_after(self, start):
        return_val = False

        while self.last_start() > start:
            return_val |= self.remove_last()

        return_val |= self.apply()

        return return_val

    def remove_ends_before(self, end):
        return_val = False

        while self.first_end() < end:
            return_val |= self.remove_first()

        return_val |= self.apply()

        return return_val

    # Removes first_start and any other starts within n-1 tiles after it.
    def shrink_start(self, n=1):
        self.solver.assert_puzzle(n <= self.last_start() - self.first_start(), f"{self} attempted to shrink start more than possible.")

        if n <= 0:
            return False

        return_val = False

        removed_start = self.first_start()
        return_val |= self.remove_first()

        while self.first_start() < removed_start + n:
            return_val |= self.remove_first()

        return_val |= self.apply()

        return return_val

    # Removes last_start and any other starts within n-1 tiles before it.
    def shrink_end(self, n=1):
        self.solver.assert_puzzle(n <= self.last_start() - self.first_start(), f"{self} attempted to shrink end more than possible.")

        if n <= 0:
            return False

        return_val = False

        removed_start = self.last_start()
        return_val |= self.remove_last()

        while self.last_start() > removed_start - n:
            return_val |= self.remove_last()

        return_val |= self.apply()

        return return_val

    def solve_self(self):
        if self.is_fixed():
            return False

        return_val = False

        for potential_run in self.potential_runs[:]:
            if potential_run not in self.potential_runs:
                continue

            # SOLVE SELF 1)
            # Trim guaranteed overlap with adjacent ClueRuns:
            # Remove any start that comes before or adjacent to prev_run.first_end()
            # or any end that comes after or adjacent to next_run.last_start().
            if self.prev_run is not None and potential_run.start <= self.prev_run.first_end():
                return_val |= self.remove_run(potential_run)
                continue
            if self.next_run is not None and potential_run.end >= self.next_run.last_start():
                return_val |= self.remove_run(potential_run)
                continue

            # SOLVE SELF 2)
            # Remove any potential run adjacent to a filled tile.
            if potential_run.next_to_filled():
                return_val |= self.remove_run(potential_run)
                continue

            # SOLVE SELF 3)
            # Remove any potential run containing a cross.
            if potential_run.contains_cross():
                return_val |= self.remove_run(potential_run)
                continue

        return_val |= self.apply()
        if self.is_fixed():
            return return_val

        # TODO:
        #  move this out of solve_self. Instead, iterate through each filled run, and check for the set of all clues
        #  (and their starts) that can contain it. The first and last in this set can adjust their bounds, then we can
        #  do "multiple ownership with minimum size" using the same set.
        # TODO:
        #  multiple ownership with minimum size
        #  - get the set of all starts from all ClueRuns that contain a given filled run
        #  - determine the tiles overlapped by all of the potential runs
        #  - can this replace regular rules for partially exclusive tiles?

        # TODO:
        #  I'm not sure if the above two TODOs still apply... I felt like no... but actually there might be a
        #  difference between filling ALL tiles overlapped, and whatever we're doing. Most likely it CAN replace regular
        #  partially exclusive rules.

        #########################################

        # SOLVE SELF 4)
        # Tighten bounds to surround the first and last exclusively owned filled tiles

        # Find the first filled run not shared by a preceding ClueRun
        first_partially_exclusive_filled = None

        for i in range(self.first_start(), self.last_end()):
            if not self.line[i].is_filled():
                continue

            run_end = find_end(self.line, i)

            if self.is_partially_exclusive_first(i, run_end):
                first_partially_exclusive_filled = i
                break

            i = run_end

        # Find the last filled run not shared by a succeeding ClueRun.
        last_partially_exclusive_filled = None

        for i in range(self.last_end() - 1, self.first_start() - 1, -1):
            if not self.line[i].is_filled():
                continue

            run_start = find_start_backward(self.line, i)

            if self.is_partially_exclusive_last(run_start, i + 1):
                last_partially_exclusive_filled = i
                break

            i = run_start - 1

        if first_partially_exclusive_filled is not None:
            # Must not start after the first filled tile which cannot be shared by a prior ClueRun.
            n = self.last_end() - (first_partially_exclusive_filled + self.length)
            return_val |= self.shrink_end(n)

        if last_partially_exclusive_filled is not None:
            # Must not end before the last filled tile which cannot be shared by a later ClueRun.
            n = (last_partially_exclusive_filled + 1 - self.length) - self.first_start()
            return_val |= self.shrink_start(n)

        self.assert_valid()

        if first_partially_exclusive_filled is not None and last_partially_exclusive_filled is not None:
            # Fill all tiles between first_exclusive_filled and last_exclusive_filled
            for i in range(first_partially_exclusive_filled, last_partially_exclusive_filled + 1):
                return_val |= fill(self.line, i)

        return_val |= self.apply()
        if self.is_fixed():
            return return_val

        #########################################

        # SOLVE SELF 5)
        # If a tile is fixed, other ClueRuns must end before or start after (with a gap).
        for i in range(self.first_start(), self.last_end()):
            if not (self.must_contain(i) or self.is_exclusive(i) and self.line[i].is_filled()):
                continue

            other_clue_run = self.prev_run
            while other_clue_run is not None:
                return_val |= other_clue_run.shrink_end(other_clue_run.last_end() - 1 - i + 2)
                other_clue_run = other_clue_run.prev_run

            other_clue_run = self.next_run
            while other_clue_run is not None:
                return_val |= other_clue_run.shrink_start(i - other_clue_run.first_start() + 2)
                other_clue_run = other_clue_run.next_run

        return_val |= self.apply()
        return return_val

    # Apply known tiles to the board
    def apply(self):
        return_val = False

        # Fill known run
        for i in range(self.last_start(), self.first_end()):
            return_val |= fill(self.line, i)

        # If the run is complete, cross the tile before and the tile after
        if self.is_fixed():
            if self.first_start() > 0:
                return_val |= cross(self.line, self.first_start() - 1)
            if self.last_end() < len(self.line):
                return_val |= cross(self.line, self.last_end())

        return return_val
