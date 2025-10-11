class State:
    CROSSED = -1
    UNKNOWN = 0
    FILLED = 1

class Axis:
    ROWS = 0
    COLS = 1

class DirtyFlag:
    NONE = 0b00
    CLUES = 0b01 # PotentialRuns have been removed from ClueRuns
    BOARD = 0b10 # New tiles have been crossed or filled
    ALL = 0b11

def board_dirty(dirty_flags):
    return DirtyFlag.BOARD & dirty_flags

def clues_dirty(dirty_flags):
    return DirtyFlag.CLUES & dirty_flags

def axis_name(axis):
    return "cols" if axis else "rows"

def axis_initial(axis):
    return "C" if axis else "R"

def line_name(axis, line_index):
    return f"{axis_initial(axis)}{line_index}"

def run_name(axis, line_index, start, end):
    return f"{line_name(axis, line_index)} {start}-{end-1}"

def tile_name(axis, line_index, tile_index):
    return f"{line_name(axis, line_index)} {tile_index}"

def clue_run_name(axis, line_index, clue_index):
    return f"{line_name(axis, line_index)}:{clue_index}"

def potential_run_name(axis, line_index, clue_index, start, end):
    return f"{clue_run_name(axis, line_index, clue_index)}@{start}-{end-1}"

def state_name(state):
    match state:
        case State.CROSSED:
            return "crossed"
        case State.UNKNOWN:
            return "unknown"
        case State.FILLED:
            return "filled"
    return str(state)

def state_name_verb(state):
    match state:
        case State.CROSSED:
            return "cross"
        case State.UNKNOWN:
            return "clear"
        case State.FILLED:
            return "fill"
    return str(state)

def puzzle_and_transpose(puzzle):
    return [puzzle, puzzle.transpose()]

# Find the index of the next tile with the given state
def find_next_start(line, i, state=State.FILLED):
    for j in range(i, len(line)):
        if line[j].is_state(state):
            return j
    return len(line)

# Find the index of the first tile in a run of same-state tiles
def find_start_backward(line, i, state=State.FILLED):
    for j in range(i, -1, -1):
        if not line[j].is_state(state):
            return j + 1
    return 0

# Find the index past the last tile in a run of same-state tiles
def find_end(line, i, state=State.FILLED):
    for j in range(i, len(line)):
        if not line[j].is_state(state):
            return j
    return len(line)

def get_run_starts_ends_lengths(puzzle_line, state=State.FILLED):
    runs = []

    end = 0
    while end != len(puzzle_line):
        start = find_next_start(puzzle_line, end, state)
        end = find_end(puzzle_line, start, state)
        length = end - start

        if length > 0:
            runs.append((start, end, length))

    return runs