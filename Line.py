from functools import partial

from helpers import *
from ClueRun import ClueRun

class Line:
    def __init__(self, solver, axis, line_index, clue_run_lengths, line_raw):
        self.solver = solver
        self.axis = axis
        self.line_index = line_index
        self.line_raw = line_raw
        self.clue_runs = []

        deduction = len(line_raw) - (sum(clue_run_lengths) + len(clue_run_lengths) - 1)

        run_start = 0
        clue_run = None
        for clue_index, run_length in enumerate(clue_run_lengths):
            clue_run = ClueRun(self, clue_index, clue_run, run_length, run_start, run_start + run_length + deduction)
            self.clue_runs.append(clue_run)
            run_start += run_length + 1

    def solve_line(self):
        dirty_flags = DirtyFlag.NONE

        # Trim any guaranteed overlap with the previous or next ClueRun
        for clue_index, clue_run in enumerate(self.clue_runs):
            dirty_flags |= self.solver.display_changes(clue_run.trim_overlap, lambda: f"Solve {clue_run}")

        trimmed_start = [False] * len(self.clue_runs)
        ends_to_trim = [-1] * len(self.clue_runs)

        # Iterate filled runs
        for start, end, length in get_run_starts_ends_lengths(self.line_raw):
            first_containing_clue_run = None
            last_containing_clue_run = None

            first_start = len(self.line_raw)
            last_start = 0
            first_end = len(self.line_raw)
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

            if last_start < start:
                # Fill guaranteed start
                dirty_flags |= self.solver.display_changes(partial(fill, self.line_raw, last_start, start),
                                                    lambda: f"Fill guaranteed start {run_name(self.axis, self.line_index, last_start, start)}")

                if last_start == first_start and first_start > 0:
                    dirty_flags |= self.solver.display_changes(partial(cross, self.line_raw, first_start - 1),
                                                        lambda: f"Cross before guaranteed start {tile_name(self.axis, self.line_index, first_start - 1)}")

            if first_end > end:
                # Fill guaranteed end
                dirty_flags |= self.solver.display_changes(partial(fill, self.line_raw, end, first_end),
                                                    lambda: f"Fill guaranteed end {run_name(self.axis, self.line_index, first_end, end)}")

                if first_end == last_end and last_end < len(self.line_raw):
                    dirty_flags |= self.solver.display_changes(partial(cross, self.line_raw, last_end),
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