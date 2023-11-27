import numpy as np

from picross_display import display_picross


def puzzle_and_transpose(puzzle):
    return [puzzle, puzzle.transpose()]


def is_filled(line, i):
    return line[i] == 1


def is_crossed(line, i):
    return line[i] == -1


def is_unknown(line, i):
    return line[i] == 0


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
        for i, puzzle_line in enumerate(puzzle_view):
            clue_run_lengths = clues_raw[i]
            clues.append(init_line_clue(clue_run_lengths, puzzle_line))


def solving_pass(puzzle, row_and_col_clues):
    for axis, puzzle_view in enumerate(puzzle_and_transpose(puzzle)):
        clues = row_and_col_clues[axis]
        for i, puzzle_line in enumerate(puzzle_view):
            line_clue = clues[i]
            for j, clue_run in enumerate(line_clue):
                # Any solving logic that does not require other clue runs
                clue_run.solve_self()
                clue_run.apply()

                # Cross all tiles between the previous run's bound_end and the current run's bound_start
                for k in range(clue_run.prev_end(), clue_run.bound_start):
                    cross(puzzle_line, k)

                # TODO: Look behind and ahead for the nearest completed run in each direction. Between those (or the
                #  beginning/end of the line) try to place runs behind the current one at the earliest spots they'll go,
                #  then trim this run's bound_start accordingly. Do the same after (at the latest spots they'll go)
                #  to trim the bound_end.

                # Sole ownership (complete): if there is a run that matches this ClueRun's length and isn't entirely
                # contained inside the previous or next ClueRun's bounds, then it must match this clue.
                # The previous ClueRun should already have its bounds trimmed down, so we can look directly after its
                # end. However, the next ClueRun's bounds may be out of date, so we will penetrate it as far as we can
                # without the run fully being contained inside it.

                overlap_end = min(clue_run.bound_end, clue_run.next_start() + clue_run.length)

                # Keep advancing this until it's the start of a filled run
                consecutive_start = clue_run.exclusive_start()

                # Only run within the exclusive section of the ClueRun
                for k in range(clue_run.exclusive_start(), overlap_end + 1):
                    # If the filled run is complete
                    if k - consecutive_start == clue_run.length:
                        clue_run.bound_start = consecutive_start
                        clue_run.bound_end = k
                        clue_run.apply()
                        break

                    if k < len(puzzle_line) and puzzle_line[k] != 1:
                        consecutive_start = k + 1

            # Cross all tiles between the last run's bound_end and end of the line
            for k in range(line_clue[-1].bound_end, len(puzzle_line)):
                cross(puzzle_line, k)


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
    def __init__(self, line, prev_run, length, bound_start, bound_end):
        self.line = line

        self.prev_run = prev_run
        if prev_run is not None:
            prev_run.next_run = self
        self.next_run = None

        self.length = length
        self.bound_start = bound_start  # first tile index
        self.bound_end = bound_end  # one beyond last tile

        self.dirty = False  # cleared every pass; if true, indicates that the run was modified this pass

    # True if the tile could potentially be part of this run
    def bound_contains(self, index):
        return self.bound_start <= index < self.bound_end

    # The length of the span of tiles that could potentially be included in this run
    def bound_length(self):
        return self.bound_end - self.bound_start

    # The number of tiles in bounds which are not part of this run
    def padding(self):
        return self.bound_length() - self.length

    # The start index of the run of tiles in the center of the bounds which are trivially known to be filled,
    # based on bounds and padding alone.
    def known_start(self):
        return self.bound_start + self.padding()

    # The end index (one past last tile) of the run of tiles in the center of the bounds which are trivially known
    # to be filled, based on bounds and padding alone.
    def known_end(self):
        return self.bound_end - self.padding()

    # True if there are any trivially known filled tiles, based on bounds and padding alone.
    def has_known(self):
        return self.known_start() < self.known_end()

    # The previous ClueRun's bound_end, or the start of the line if this is the first
    def prev_end(self):
        if self.prev_run is None:
            return 0
        return self.prev_run.bound_end

    # The next ClueRun's bound_start, or the end of the line if this is the last
    def next_start(self):
        if self.next_run is None:
            return len(self.line)
        return self.next_run.bound_start

    # The start index of the section that is not overlapping with the previous clue, if any
    def exclusive_start(self):
        return max(self.bound_start, self.prev_end())

    # The end index (one past last tile) of the section that is not overlapping with the next clue, if any
    def exclusive_end(self):
        return min(self.bound_end, self.next_start())

    # True if there is a section that is not overlapping with any other clues, regardless of whether the tiles in
    # the section are filled.
    def has_exclusive(self):
        return self.exclusive_start() < self.exclusive_end()

    # True if all tiles in this run are known
    def is_complete(self):
        return self.bound_length() == self.length

    # Increases bound_start by n, and fills any new known tiles as a result
    def shrink_start(self, n=1):
        if n < 0 or n > self.padding():
            assert False

        if n == 0:
            return

        for i in range(n):
            self.bound_start += 1

            # If a tile is known to be filled as a result, fill it
            if self.has_known():
                fill(self.line, self.known_end() - 1)

        self.dirty = True

    # Decreases bound_end by n, and fills any new known tiles as a result
    def shrink_end(self, n=1):
        if n < 0 or n > self.padding():
            assert False

        if n == 0:
            return

        for i in range(n):
            self.bound_end -= 1

            # If a tile is known to be filled as a result, fill it
            if self.has_known():
                fill(self.line, self.known_start())

        self.dirty = True

    def solve_self(self):
        if self.is_complete():
            return

        # SOLVE SELF 1)
        # Expand known start to any filled tiles immediately before the current known start
        while self.has_known() and self.known_start() > self.bound_start and is_filled(self.line, self.known_start() - 1):
            self.shrink_end()  # Shrinking end is same as expanding known start

            if self.is_complete():
                return

        # SOLVE SELF 1)
        # Expand known end to any filled tiles immediately after the current known start
        while self.has_known() and self.known_end() < self.bound_start and is_filled(self.line, self.known_end()):
            self.shrink_start()  # Shrinking start is same as expanding known end

            if self.is_complete():
                return

        # SOLVE SELF 2)
        # Shrink bound start while placement at the first position would make this run adjacent to another fill
        # TODO: support any position and subdivide on this
        while self.bound_start > 0 and is_filled(self.line, self.bound_start - 1)\
                or is_filled(self.line, self.bound_start + self.length):
            self.shrink_start()

            if self.is_complete():
                return

        # SOLVE SELF 2)
        # Shrink bound end while placement at the last position would make this run adjacent to another fill
        # TODO: support any position and subdivide on this
        while self.bound_end < len(self.line) and is_filled(self.line, self.bound_end)\
                or is_filled(self.line, self.bound_end - 1 - self.length):
            self.shrink_end()

            if self.is_complete():
                return

        # SOLVE SELF 3)
        # Shrink bound while placement at the first position would overlap a cross
        # TODO: support any position and subdivide on this
        i = self.bound_start
        while i < self.bound_start + self.length:
            if is_crossed(self.line, i):
                self.shrink_start(i - self.bound_start + 1)
            i += 1

            if self.is_complete():
                return

        # SOLVE SELF 3)
        # Shrink bound while placement at the last position would overlap a cross
        # TODO: support any position and subdivide on this
        i = self.bound_end - 1
        while i > self.bound_end - 1 - self.length:
            if is_crossed(self.line, i):
                self.shrink_end(self.bound_end - i)
            i -= 1

            if self.is_complete():
                return

        # Find the first and last filled tile within the solely-owned bounds
        first_sole_filled = None
        last_sole_filled = None

        for i in range(self.exclusive_start(), self.exclusive_end()):
            if is_filled(self.line, i):
                last_sole_filled = i
                if first_sole_filled is None:
                    first_sole_filled = i

        # SOLVE SELF 4)
        # Trim bounds around the first and last filled tiles in the sole ownership bounds
        # TODO: multiple ownership with minimum size
        if first_sole_filled is not None and last_sole_filled is not None and first_sole_filled <= last_sole_filled:
            self.bound_start = max(self.bound_start, last_sole_filled + 1 - self.length)
            self.bound_end = min(self.bound_end, first_sole_filled + self.length)

            if self.bound_start >= self.bound_end:
                assert False

            # Fill all tiles between first_sole_filled and last_sole_filled
            for i in range(first_sole_filled, last_sole_filled + 1):
                fill(self.line, i)

            if self.is_complete():
                return

    # Apply known tiles to the board
    def apply(self):
        # Fill known run
        for i in range(self.known_start(), self.known_end()):
            fill(self.line, i)

        # If the run is complete, cross the tile before and the tile after
        if self.is_complete():
            if self.known_start() > 0:
                cross(self.line, self.known_start() - 1)
            if self.known_end() < len(self.line):
                cross(self.line, self.known_end())
