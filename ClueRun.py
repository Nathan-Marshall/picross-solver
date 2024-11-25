from helpers import *


class ClueRun:
    def __init__(self, line, prev_run, length, first_start, last_end):
        self.line = line

        self.prev_run = prev_run
        if prev_run is not None:
            prev_run.next_run = self
        self.next_run = None

        self.length = length
        self.starts = [i for i in range(first_start, last_end - length + 1)]

        self.dirty = False  # cleared every pass; if true, indicates that the run was modified this pass

    # Index of the first tile of the run in the first possible position
    def first_start(self):
        return self.starts[0]

    # Index of the first tile of the run in the last possible position
    def last_start(self):
        return self.starts[-1]

    # Index past the last tile of a run, given the start tile
    def end(self, start):
        return start + self.length

    # Index past the last tile of the run in the first possible position
    def first_end(self):
        return self.end(self.first_start())

    # Index past the last tile of the run in the last possible position
    def last_end(self):
        return self.end(self.last_start())

    # True if the entire given run of tiles would be part of this run, assuming this run starts at the given start.
    def contains_with_start(self, start, run_start, run_end=None):
        if run_end is None:
            run_end = run_start + 1

        return start <= run_start < run_end <= self.end(start)

    # True if the entire given run of tiles would be part of this run for any of the possible start positions
    def can_contain(self, run_start, run_end=None):
        if run_end is None:
            run_end = run_start + 1

        if run_end - run_start > self.length:
            return False

        for start in self.starts:
            if start > run_start:
                break

            if run_end <= self.end(start):
                return True

        return False

    # True if the entire given run of tiles is part of this run for every possible start position
    def must_contain(self, run_start, run_end=None):
        if run_end is None:
            run_end = run_start + 1

        # Return false if this ClueRun can't contain this index
        if not self.can_contain(run_start, run_end):
            return False

        for start in self.starts:
            if not self.contains_with_start(start, run_start, run_end):
                return False

        return True

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

        # Return false if this ClueRun can't contain this run
        if not self.can_contain(run_start, run_end):
            return False

        # Return false if any of the previous ClueRuns can contain this run
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

        # Return false if this ClueRun can't contain this run
        if not self.can_contain(run_start, run_end):
            return False

        # Return false if any of the next ClueRuns can contain this run
        clue_run = self.next_run
        while clue_run is not None:
            if clue_run.can_contain(run_start, run_end):
                return False
            clue_run = clue_run.next_run

        return True

    # Assuming this ClueRun starts at the given start, return true if the resulting run would contain a cross
    def contains_cross_with_start(self, start):
        for i in range(start, self.end(start)):
            if is_crossed(self.line, i):
                return True
        return False

    # Assuming this ClueRun starts at the given start, return true if the resulting run would be adjacent to another
    # filled tile
    def run_too_long_with_start(self, start):
        if start > 0 and is_filled(self.line, start - 1):
            return True

        if self.end(start) < len(self.line) and is_filled(self.line, self.end(start)):
            return True

        return False

    # True if there is only one possible start position for this run
    def is_fixed(self):
        return len(self.starts) == 1

    # Removes first_start and any other starts within n-1 tiles after it.
    def shrink_start(self, n=1):
        if n > self.last_start() - self.first_start():
            assert False

        if n <= 0:
            return

        removed_start = self.starts.pop(0)

        while self.first_start() < removed_start + n:
            self.starts.pop(0)

        self.dirty = True
        self.apply()

    # Removes last_start and any other starts within n-1 tiles before it.
    def shrink_end(self, n=1):
        if n > self.last_start() - self.first_start():
            assert False

        if n <= 0:
            return

        removed_start = self.starts.pop()

        while self.last_start() > removed_start - n:
            self.starts.pop()

        self.dirty = True
        self.apply()

    def solve_self(self):
        if self.is_fixed():
            return

        for start in self.starts:
            # SOLVE SELF 1)
            # Remove any start that comes before or adjacent to prev_run.first_end()
            # or any end that comes after or adjacent to next_run.last_start().
            if self.prev_run is not None and start <= self.prev_run.first_end():
                self.starts.remove(start)
                self.dirty = True
                continue
            if self.next_run is not None and self.end(start) >= self.next_run.last_start():
                self.starts.remove(start)
                self.dirty = True
                continue

            # SOLVE SELF 2)
            # Remove any start where the resulting run would be adjacent to another filled tile.
            if self.run_too_long_with_start(start):
                self.starts.remove(start)
                self.dirty = True
                continue

            # SOLVE SELF 3)
            # Remove any start where the resulting run would contain a cross.
            if self.contains_cross_with_start(start):
                self.starts.remove(start)
                self.dirty = True
                continue

        self.apply()
        if self.is_fixed():
            return

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
        #  if filled run is same length as all owners, but owner is unknown, cross extremities
        # TODO:
        #  Consider the union between this ClueRun's starts and the prev_run's starts.
        #  - For every combination of starts which are in sequence and the resulting runs are not overlapping, all
        #  filled tiles exclusively owned by the compound must be contained within the resulting runs, otherwise discard
        #  that combination of start-ClueRun pairs. If a start-ClueRun pair is not included in any of the valid
        #  combinations, then discard that start from that ClueRun.
        #  - After finishing all combinations. Do it again, but include prev_run.prev_run as well, and so on.
        #  - If a line is complete, it will be covered by this rule.

        # SOLVE SELF 5)
        # If a tile is fixed, other ClueRuns before must end before or start after (with a gap).
        for i in range(self.first_start(), self.last_end()):
            if not (self.must_contain(i) or self.is_exclusive(i) and is_filled(self.line, i)):
                continue

            other_clue_run = self.prev_run
            while other_clue_run is not None:
                other_clue_run.shrink_end(other_clue_run.last_end() - 1 - i + 2)
                other_clue_run = other_clue_run.prev_run

            other_clue_run = self.next_run
            while other_clue_run is not None:
                other_clue_run.shrink_start(i - other_clue_run.first_start() + 2)
                other_clue_run = other_clue_run.next_run

    # Apply known tiles to the board
    def apply(self):
        # Fill known run
        for i in range(self.last_start(), self.first_end()):
            fill(self.line, i)

        # If the run is complete, cross the tile before and the tile after
        if self.is_fixed():
            if self.last_start() > 0:
                cross(self.line, self.last_start() - 1)
            if self.first_end() < len(self.line):
                cross(self.line, self.first_end())
