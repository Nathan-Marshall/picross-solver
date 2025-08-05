import colorsys
import random

from helpers import State, Axis
import numpy as np
from matplotlib import pyplot as plt
from matplotlib.widgets import Button

def display_picross(solver_base, title=None, block=True, btn_solve_callback=None):
    if not title:
        title = solver_base.puzzle_name

    # Convert the puzzle to a numpy array
    puzzle_array = np.array(solver_base.puzzle_raw)
    num_rows = puzzle_array.shape[Axis.ROWS]
    num_cols = puzzle_array.shape[Axis.COLS]

    # Create a figure and a set of subplots
    fig, ax = plt.subplots(figsize=(6, 6))
    fig.canvas.manager.set_window_title(title)
    fig.set_facecolor('black')

    # Display the puzzle as an image
    # Use a custom color map
    cmap = plt.cm.colors.ListedColormap(['grey', 'grey', 'black'])
    bounds = [-2, -0.5, 0.5, 2]
    norm = plt.cm.colors.BoundaryNorm(bounds, cmap.N)
    ax.imshow(puzzle_array, cmap=cmap, norm=norm)

    # Draw grid lines
    ax.set_xticks(np.arange(-.5, num_cols, 1), minor=False)
    ax.set_yticks(np.arange(-.5, num_rows, 1), minor=False)
    ax.grid(which='major', color='#444', linestyle='-', linewidth=2)
    ax.set_axisbelow(True)

    ax.set_xticks(np.arange(-.5, num_cols, 1), minor=True)
    ax.set_yticks(np.arange(-.5, num_rows, 1), minor=True)
    ax.grid(which='minor', color='#444', linestyle='-', linewidth=2)
    ax.set_axisbelow(True)

    # Add row clues
    for i, clue in enumerate(solver_base.row_and_col_clues[Axis.ROWS]):
        first_hue = random.random()
        for j, clue_run in enumerate(reversed(clue)):
            hue = first_hue + j / len(clue)
            sat = 0 if clue_run.is_fixed() else 1
            if not hasattr(clue_run, 'color'):
                clue_run.color = colorsys.hls_to_rgb(hue, .5, sat)

            ax.text(-1 - j / 2, i, str(clue_run.length), ha='center', va='center', fontsize=16, color=clue_run.color)

    # Add column clues
    for i, clue in enumerate(solver_base.row_and_col_clues[Axis.COLS]):
        first_hue = random.random()
        for j, clue_run in enumerate(reversed(clue)):
            hue = first_hue + j / len(clue)
            sat = 0 if clue_run.is_fixed() else 1
            if not hasattr(clue_run, 'color'):
                clue_run.color = colorsys.hls_to_rgb(hue, .5, sat)

            ax.text(i, -1 - j / 2, str(clue_run.length), ha='center', va='center', fontsize=16, color=clue_run.color)

    # Draw an 'X' for each tile with an underlying value of -1
    cross_radius = 0.35
    for row in range(num_rows):
        for col in range(num_cols):
            if solver_base.puzzle_raw[row][col] == -1:
                ax.plot([col - cross_radius, col + cross_radius], [row - cross_radius, row + cross_radius], color='black')
                ax.plot([col - cross_radius, col + cross_radius], [row + cross_radius, row - cross_radius], color='black')

    # Draw each ClueRun overlay
    for axis, line_index, line_clue in solver_base.enumerate_all_line_clues():
        for clue_index, clue_run in enumerate(line_clue):
            draw_clue_run(ax, clue_run, line_index, clue_index, len(line_clue), axis)

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
    if clue_run.is_fixed():
        return

    # offset each run's line so that overlapping bounds are visible
    offset = line_index + 0.8 * ((run_index + 1) / (num_runs + 1) - 0.5)

    # Draw the main line along the entire length of the bounds, dashed in the unknown sections
    for i in range(clue_run.first_start(), clue_run.last_end()):
        if not clue_run.can_contain(i):
            continue

        linestyle = 'solid' if clue_run.must_contain(i) else 'dashed'
        line_start = i - 0.3 if not clue_run.can_contain(i-1) or clue_run.length == 1 else i - 0.5
        line_end = i + 0.3 if not clue_run.can_contain(i+1) or clue_run.length == 1 else i + 0.5
        plot_with_axis_swap(ax, vertical,
                            [line_start, line_end],
                            [offset, offset],
                            color=clue_run.color, linestyle=linestyle)

    # Draw small arrows to indicate each potential start and end
    for potential_run in clue_run.potential_runs:
        plot_arrow(ax, vertical, False, potential_run.start - 0.4, offset, clue_run.color)
        plot_arrow(ax, vertical, True, (potential_run.end - 1) + 0.4, offset, clue_run.color)

    # Fill in the last start and first end arrows a little, to help indicate where the center known section is
    plot_with_axis_swap(ax, vertical,
                        [clue_run.last_start() - 0.4, clue_run.last_start() - 0.4],
                        [offset - 0.1, offset + 0.1],
                        color=clue_run.color)
    plot_with_axis_swap(ax, vertical,
                        [(clue_run.first_end() - 1) + 0.4, (clue_run.first_end() - 1) + 0.4],
                        [offset - 0.1, offset + 0.1],
                        color=clue_run.color)

def plot_with_axis_swap(ax, swap, *args, **kwargs):
    if swap:
        temp_list = list(args)
        temp_list[0], temp_list[1] = temp_list[1], temp_list[0]
        args = tuple(temp_list)

    ax.plot(*args, **kwargs)

def plot_arrow(ax, vertical, flip, on_axis_offset, cross_axis_offset, color):
    plot_with_axis_swap(ax, vertical,
                        [on_axis_offset, on_axis_offset + (-0.1 if flip else 0.1), on_axis_offset],
                        [cross_axis_offset - 0.1, cross_axis_offset, cross_axis_offset + 0.1],
                        color=color)

def block_until_windows_closed():
    plt.show()