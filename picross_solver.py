import numpy as np

from picross_display import display_picross

CROSSED = -1
UNKNOWN = 0
FILLED = 1


def puzzle_and_transpose(puzzle):
    return [puzzle, puzzle.transpose()]


def is_filled(line, i):
    return line[i] == FILLED


def is_crossed(line, i):
    return line[i] == CROSSED


def is_unknown(line, i):
    return line[i] == UNKNOWN


def is_known(line, i):
    return not is_unknown(line, i)


def fill(line, i):
    if is_filled(line, i):
        return

    if is_crossed(line, i):
        assert False

    line[i] = 1


def cross(line, i):
    if is_crossed(line, i):
        return

    if is_filled(line, i):
        assert False

    line[i] = -1


# Find the index of the first tile in a run of like tiles
def find_start(line, i, tile_type=FILLED):
    for j in range(i, -1, -1):
        if line[j] != tile_type:
            return j + 1
    return 0


# Find the index past the last tile in a run of like tiles
def find_end(line, i, tile_type=FILLED):
    for j in range(i, len(line)):
        if line[j] != tile_type:
            return j
    return len(line)


def solve(puzzle, row_and_col_clues, row_and_col_clues_raw, display_steps=False):
    initial_solving_pass(puzzle, row_and_col_clues, row_and_col_clues_raw)

    if display_steps:
        display_picross(puzzle, row_and_col_clues, block=False)

    puzzle_copy = np.array((0, 0))
    while not np.array_equal(puzzle, puzzle_copy) or has_dirty_clue_runs(row_and_col_clues):
        puzzle_copy = puzzle.copy()
        clean_all_clue_runs(row_and_col_clues)

        solving_pass(puzzle, row_and_col_clues)

        if display_steps:
            display_picross(puzzle, row_and_col_clues, block=False)

    return verify(puzzle, row_and_col_clues_raw)


def verify(puzzle, row_and_col_clues_raw):
    for axis, puzzle_view in enumerate(puzzle_and_transpose(puzzle)):
        clues_raw = row_and_col_clues_raw[axis]
        for line_index, puzzle_line in enumerate(puzzle_view):
            clue_run_lengths = clues_raw[line_index]
            if not verify_line(puzzle_line, clue_run_lengths):
                return False
    return True


def verify_line(puzzle_line, clue_run_lengths):
    # All tiles must be known
    for tile in puzzle_line:
        if tile == UNKNOWN:
            return False

    prev_run_end = 0
    for clue_run_length in clue_run_lengths:
        # Find the start of the next run
        run_start = find_end(puzzle_line, prev_run_end, tile_type=CROSSED)

        # Reached the end of the line without encountering the run
        if run_start == len(puzzle_line):
            return False

        # Find the end of the run
        run_end = find_end(puzzle_line, run_start)

        # Verify that the run was the correct length
        if run_end != run_start + clue_run_length:
            return False

        prev_run_end = run_end

    # Verify that it's all crosses until the end of the line
    line_end = find_end(puzzle_line, prev_run_end, tile_type=CROSSED)
    return line_end == len(puzzle_line)




def init_line_clue(line_clue_run_lengths, line):
    line_clue = []
    deduction = len(line) - (sum(line_clue_run_lengths) + len(line_clue_run_lengths) - 1)

    run_start = 0
    clue_run = None
    for run_length in line_clue_run_lengths:
        clue_run = ClueRun(line, clue_run, run_length, run_start, run_start + run_length + deduction)
        clue_run.apply()
        line_clue.append(clue_run)
        run_start += run_length + 1

    return line_clue


def initial_solving_pass(puzzle, row_and_col_clues, row_and_col_clues_raw):
    for axis, puzzle_view in enumerate(puzzle_and_transpose(puzzle)):
        clues = row_and_col_clues[axis]
        clues_raw = row_and_col_clues_raw[axis]
        for line_index, puzzle_line in enumerate(puzzle_view):
            clue_run_lengths = clues_raw[line_index]
            clues.append(init_line_clue(clue_run_lengths, puzzle_line))


def solving_pass(puzzle, row_and_col_clues):
    for axis, puzzle_view in enumerate(puzzle_and_transpose(puzzle)):
        clues = row_and_col_clues[axis]
        for line_index, puzzle_line in enumerate(puzzle_view):
            line_clue = clues[line_index]
            solve_line(puzzle_line, line_clue)


def solve_line(puzzle_line, line_clue):
    for run_index, clue_run in enumerate(line_clue):
        # Any solving logic that does not require other clue runs
        clue_run.solve_self()
        clue_run.apply()

    # Cross tiles that are not part of any ClueRuns
    cross_unclaimed_tiles(puzzle_line, line_clue)


# If a tile is guaranteed not to be part of any run in the line, cross it out
def cross_unclaimed_tiles(line, line_clue):
    for i in range(len(line)):
        if is_known(line, i):
            continue

        can_contain = False
        for clue_run in line_clue:
            if clue_run.can_contain(i):
                can_contain = True
                break

        if not can_contain:
            cross(line, i)


def has_dirty_clue_runs(row_and_col_clues):
    for axis_clues in row_and_col_clues:
        for line_clue in axis_clues:
            for clue_run in line_clue:
                if clue_run.dirty:
                    return True
    return False


def clean_all_clue_runs(row_and_col_clues):
    for axis_clues in row_and_col_clues:
        for line_clue in axis_clues:
            for clue_run in line_clue:
                clue_run.dirty = False


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

        # SOLVE SELF 4)
        # Tighten bounds to surround the first and last exclusively owned filled tiles

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

        # Find the first filled run not shared by a preceding ClueRun
        first_partially_exclusive_filled = None

        for i in range(self.first_start(), self.last_end()):
            if not is_filled(self.line, i):
                continue

            run_end = find_end(self.line, i)

            if self.is_partially_exclusive_first(i, run_end):
                first_partially_exclusive_filled = i
                break

            i = run_end

        # Find the last filled run not shared by a succeeding ClueRun.
        last_partially_exclusive_filled = None

        for i in range(self.last_end() - 1, self.first_start() - 1, -1):
            if not is_filled(self.line, i):
                continue

            run_start = find_start(self.line, i)

            if self.is_partially_exclusive_last(run_start, i + 1):
                last_partially_exclusive_filled = i
                break

            i = run_start - 1

        if first_partially_exclusive_filled is not None:
            # Must not start after the first filled tile which cannot be shared by a prior ClueRun.
            n = self.last_end() - (first_partially_exclusive_filled + self.length)
            self.shrink_end(n)

        if last_partially_exclusive_filled is not None:
            # Must not end before the last filled tile which cannot be shared by a later ClueRun.
            n = (last_partially_exclusive_filled + 1 - self.length) - self.first_start()
            self.shrink_start(n)

        if len(self.starts) == 0:
            assert False

        if first_partially_exclusive_filled is not None and last_partially_exclusive_filled is not None:
            # Fill all tiles between first_exclusive_filled and last_exclusive_filled
            for i in range(first_partially_exclusive_filled, last_partially_exclusive_filled + 1):
                fill(self.line, i)

        self.apply()
        if self.is_fixed():
            return

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
