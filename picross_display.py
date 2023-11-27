import colorsys
import random

import numpy as np
from matplotlib import pyplot as plt
from matplotlib.widgets import Button


def display_picross(puzzle, row_and_col_clues, block=True, btn_solve_callback=None):
    # Convert the puzzle to a numpy array
    puzzle_array = np.array(puzzle)

    # Create a figure and a set of subplots
    fig, ax = plt.subplots(figsize=(6, 6))
    fig.set_facecolor('black')

    # Display the puzzle as an image
    # Use a custom color map to display -1 values as white
    cmap = plt.cm.colors.ListedColormap(['grey', 'grey', 'black'])
    bounds = [-2, -0.5, 0.5, 2]
    norm = plt.cm.colors.BoundaryNorm(bounds, cmap.N)
    ax.imshow(puzzle_array, cmap=cmap, norm=norm)

    # Draw grid lines
    ax.set_xticks(np.arange(-.5, len(puzzle[0]), 1), minor=True)
    ax.set_yticks(np.arange(-.5, len(puzzle), 1), minor=True)
    ax.grid(which='minor', color='#444', linestyle='-', linewidth=2)
    ax.set_axisbelow(True)

    # Add row clues
    for i, clue in enumerate(row_and_col_clues[0]):
        first_hue = random.random()
        for j, clue_run in enumerate(reversed(clue)):
            hue = first_hue + j / len(clue)
            sat = 0 if clue_run.is_complete() else 1
            if not hasattr(clue_run, 'color'):
                clue_run.color = colorsys.hls_to_rgb(hue, .5, sat)

            ax.text(-1 - j / 3, i, str(clue_run.length), ha='center', va='center', fontsize=16, color=clue_run.color)

    # Add column clues
    for i, clue in enumerate(row_and_col_clues[1]):
        first_hue = random.random()
        for j, clue_run in enumerate(reversed(clue)):
            hue = first_hue + j / len(clue)
            sat = 0 if clue_run.is_complete() else 1
            if not hasattr(clue_run, 'color'):
                clue_run.color = colorsys.hls_to_rgb(hue, .5, sat)

            ax.text(i, -1 - j / 3, str(clue_run.length), ha='center', va='center', fontsize=16, color=clue_run.color)

    # Draw an 'X' for each tile with an underlying value of -1
    for i in range(len(puzzle)):
        for j in range(len(puzzle[i])):
            if puzzle[i][j] == -1:
                ax.plot([j - 0.5, j + 0.5], [i - 0.5, i + 0.5], color='black')
                ax.plot([j - 0.5, j + 0.5], [i + 0.5, i - 0.5], color='black')

    # Draw a rectangle outline for each ClueRun object
    for axis in range(2):
        for i, clue in enumerate(row_and_col_clues[axis]):
            for j, clue_run in enumerate(clue):
                draw_clue_run(ax, clue_run, i, j, len(clue), axis)

    # Hide the x and y axis labels and ticks
    ax.set_xticklabels([])
    ax.set_yticklabels([])
    ax.tick_params(which='both', bottom=False, left=False)

    # Adjust layout to make room for clues
    fig.tight_layout()

    # Add button which will attempt to solve the puzzle. Can be used to do additional passes for debugging.
    ax_solve = fig.add_axes([0.05, 0.05, 0.1, 0.075])
    btn_solve = Button(ax_solve, 'Solve')
    btn_solve.on_clicked(lambda event: btn_solve_callback())

    # Show the plot
    plt.show(block=block)


def draw_clue_run(ax, clue_run, line_index, run_index, num_runs, vertical):
    if clue_run.is_complete():
        return

    # offset each run's line so that overlapping bounds are visible
    offset = line_index + 0.8 * ((run_index + 1) / (num_runs + 1) - 0.5)

    bounds_start = clue_run.bound_start - 0.4
    bounds_end = clue_run.bound_end - 1 + 0.4
    known_start = clue_run.known_start() - 0.4
    known_end = clue_run.known_end() - 1 + 0.4

    # Draw the main line along the entire length of the bounds, dashed in the unknown sections
    if clue_run.has_known():
        plot_with_axis_swap(ax, vertical,
                            [bounds_start, known_start],
                            [offset, offset],
                            color=clue_run.color, linestyle='--')

        plot_with_axis_swap(ax, vertical,
                            [known_start, known_end],
                            [offset, offset],
                            color=clue_run.color)

        plot_with_axis_swap(ax, vertical,
                            [known_end, bounds_end],
                            [offset, offset],
                            color=clue_run.color, linestyle='--')
    else:
        plot_with_axis_swap(ax, vertical,
                            [bounds_start, bounds_end],
                            [offset, offset],
                            color=clue_run.color, linestyle='--')

    # Draw small arrows to indicate where the known tiles start and stop
    plot_with_axis_swap(ax, vertical,
                        [known_start, known_start + 0.1, known_start],
                        [offset - 0.1, offset, offset + 0.1],
                        color=clue_run.color)

    plot_with_axis_swap(ax, vertical,
                        [known_end, known_end - 0.1, known_end],
                        [offset - 0.1, offset, offset + 0.1],
                        color=clue_run.color)


def plot_with_axis_swap(ax, swap, *args, **kwargs):
    if swap:
        temp_list = list(args)
        temp_list[0], temp_list[1] = temp_list[1], temp_list[0]
        args = tuple(temp_list)

    ax.plot(*args, **kwargs)


def block_until_windows_closed():
    plt.show()
