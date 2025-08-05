CROSSED = -1
UNKNOWN = 0
FILLED = 1

def puzzle_and_transpose(puzzle):
    return [puzzle, puzzle.transpose()]

def set_state(state, line, start, end=None):
    if end is None:
        end = start + 1

    return_val = False

    for tile in line[start:end]:
        return_val |= tile.set_state(state)

    return return_val

def fill(line, start, end=None):
    return set_state(State.FILLED, line, start, end)

def cross(line, start, end=None):
    return set_state(State.CROSSED, line, start, end)

# Find the index of the next tile with the given state
def find_next_start(line, i, state=FILLED):
    for j in range(i, len(line)):
        if line[j].get_state() == state:
            return j
    return len(line)

# Find the index of the first tile in a run of same-state tiles
def find_start_backward(line, i, state=FILLED):
    for j in range(i, -1, -1):
        if line[j].get_state() != state:
            return j + 1
    return 0

# Find the index past the last tile in a run of same-state tiles
def find_end(line, i, state=FILLED):
    for j in range(i, len(line)):
        if line[j].get_state() != state:
            return j
    return len(line)

def get_run_starts_ends_lengths(puzzle_line, state=FILLED):
    runs = []

    end = 0
    while end != len(puzzle_line):
        start = find_next_start(puzzle_line, end, state)
        end = find_end(puzzle_line, start, state)
        length = end - start

        if length > 0:
            runs.append((start, end, length))

    return runs