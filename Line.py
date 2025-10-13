from functools import partial
from line_profiler_pycharm import profile

from helpers import *
from ClueRun import ClueRun

class Line:
    def __init__(self, solver, axis, line_index, clue_run_lengths, puzzle_line):
        self.solver = solver
        self.axis = axis
        self.line_index = line_index
        self.clue_run_lengths = clue_run_lengths
        self.puzzle_line = puzzle_line
        self.clue_runs = []
        self.filled_runs = []

        deduction = len(puzzle_line) - (sum(clue_run_lengths) + len(clue_run_lengths) - 1)

        run_start = 0
        clue_run = None
        for clue_index, run_length in enumerate(clue_run_lengths):
            clue_run = ClueRun(self, clue_index, clue_run, run_length, run_start, run_start + run_length + deduction)
            self.clue_runs.append(clue_run)
            run_start += run_length + 1

    def verify(self):
        for (start, end), length in zip(self.filled_runs, self.clue_run_lengths):
            if end - start != length:
                return False
        return True

    def set_state(self, state, start, end=None):
        if end is None:
            end = start + 1

        dirty_flags = DirtyFlag.NONE

        for tile in self.puzzle_line[start:end]:
            dirty_flags |= tile.set_state(state, fill_axis=self.axis)

        if state == State.FILLED and board_dirty(dirty_flags):
            self.add_filled_run(start, end)

        return dirty_flags

    def fill(self, start, end=None):
        return self.set_state(State.FILLED, start, end)

    def cross(self, start, end=None):
        return self.set_state(State.CROSSED, start, end)

    def add_filled_run(self, start, end=None):
        if end is None:
            end = start + 1

        connected_or_added_index = None
        i = 0
        while i < len(self.filled_runs):
            existing_start, existing_end = self.filled_runs[i]
            if existing_start <= end and existing_end >= start:
                if connected_or_added_index is None:
                    self.filled_runs[i] = (min(existing_start, start), max(existing_end, end))
                    connected_or_added_index = i
                else:
                    connected_start, connected_end = self.filled_runs[connected_or_added_index]
                    self.filled_runs[connected_or_added_index] = (min(existing_start, connected_start), max(existing_end, connected_end))
                    self.filled_runs.pop(i)
                    continue
            elif existing_start > end:
                if connected_or_added_index is None:
                    self.filled_runs.insert(i, (start, end))
                    connected_or_added_index = i
                break
            i += 1

        if connected_or_added_index is None:
            self.filled_runs.append((start, end))

    def solve_line(self):
        dirty_flags = DirtyFlag.NONE

        # Trim any guaranteed overlap with the previous or next ClueRun
        for clue_index, clue_run in enumerate(self.clue_runs):
            dirty_flags |= self.solver.display_changes(clue_run.trim_overlap, lambda: f"Solve {clue_run}")

        trimmed_start = [False] * len(self.clue_runs)
        ends_to_trim = [-1] * len(self.clue_runs)

        # Iterate filled runs
        for start, end in self.filled_runs[:]:
            first_containing_clue_run = None
            last_containing_clue_run = None

            first_start = len(self.puzzle_line)
            last_start = 0
            first_end = len(self.puzzle_line)
            last_end = 0

            # Iterate all potential runs containing the filled run, from all ClueRuns
            for clue_run in self.clue_runs:
                containing_potential_runs = clue_run.get_containing_potential_runs(start, end)

                if not containing_potential_runs:
                    continue

                if first_containing_clue_run is None:
                    first_containing_clue_run = clue_run
                last_containing_clue_run = clue_run

                for potential_run in containing_potential_runs:
                    first_start = min(first_start, potential_run.start)
                    last_start = max(last_start, potential_run.start)
                    first_end = min(first_end, potential_run.end)
                    last_end = max(last_end, potential_run.end)

            new_start = last_start if last_start < start else end
            new_end = first_end if first_end > end else start

            if new_start < new_end:
                # Fill guaranteed run
                dirty_flags |= self.solver.display_changes(partial(self.fill, new_start, new_end),
                                                           lambda: f"Fill guaranteed run {run_name(self.axis, self.line_index, new_start, new_end)}")

            if last_start < start and last_start == first_start and first_start > 0:
                dirty_flags |= self.solver.display_changes(partial(self.cross, first_start - 1),
                                                               lambda: f"Cross before guaranteed start {tile_name(self.axis, self.line_index, first_start - 1)}")

            if first_end > end and first_end == last_end and last_end < len(self.puzzle_line):
                dirty_flags |= self.solver.display_changes(partial(self.cross, last_end),
                                                               lambda: f"Cross after guaranteed end {tile_name(self.axis, self.line_index, last_end)}")

            # The first clue run that can contain this run must not start after the run does.
            if not trimmed_start[first_containing_clue_run.clue_index]:
                dirty_flags |= self.solver.display_changes(partial(first_containing_clue_run.remove_starts_after, start),
                                                    lambda: f"{first_containing_clue_run} first to contain {run_name(self.axis, self.line_index, start, end)} so last_start={start}")
                trimmed_start[first_containing_clue_run.clue_index] = True

            # The last clue run that can contain this run must not end before the run does. (mark it for now)
            ends_to_trim[last_containing_clue_run.clue_index] = end

        # Trim any marked ClueRun to the end of the last filled run for which it was the last ClueRun to contain.
        for clue_index, clue_run in enumerate(self.clue_runs):
            if ends_to_trim[clue_index] != -1:
                end = ends_to_trim[clue_index]
                dirty_flags |= self.solver.display_changes(partial(clue_run.remove_ends_before, end),
                                                    lambda: f"{clue_run} last to contain {run_name(self.axis, self.line_index, start, end)} so first_end={end}")

        return dirty_flags