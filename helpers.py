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


def fill(line, start, end=None):
    if end is None:
        end = start + 1

    for i in range(start, end):
        if is_filled(line, i):
            continue

        assert not is_crossed(line, i)

        line[i] = FILLED


def cross(line, start, end=None):
    if end is None:
        end = start + 1

    for i in range(start, end):
        if is_crossed(line, i):
            continue

        assert not is_filled(line, i)

        line[i] = CROSSED


# Find the index of the next tile of the given type
def find_next_start(line, i, tile_type=FILLED):
    for j in range(i, len(line)):
        if line[j] == tile_type:
            return j
    return len(line)


# Find the index of the first tile in a run of like tiles
def find_start_backward(line, i, tile_type=FILLED):
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


def get_run_starts_ends_lengths(puzzle_line, tile_type=FILLED):
    runs = []

    end = 0
    while end != len(puzzle_line):
        start = find_next_start(puzzle_line, end, tile_type)
        end = find_end(puzzle_line, start, tile_type)
        length = end - start

        if length > 0:
            runs.append((start, end, length))

    return runs

