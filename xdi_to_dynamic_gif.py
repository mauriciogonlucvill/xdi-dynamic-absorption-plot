#!/usr/bin/env python3
"""
Create an animated GIF from an XDI absorption spectrum.

The script reads an .xdi file, extracts numeric columns, and builds an
animated plot where the curve appears progressively.

Default behavior:
- x column: first numeric column
- y column: second numeric column, unless another column is selected with --y-col
- uses generic axis labels by default: Energy (eV) and Absorption (a.u.)
- can optionally use labels inferred from XDI column metadata with --use-xdi-labels
- ignores header/comment lines that start with '#'
- exports a looping GIF and a final preview PNG

Requirements:
- Python 3.10 or newer

Speed modes:
- index: advances by data index / row number.
- x: advances with approximately constant speed along the x axis.
- arc: advances with approximately constant visual speed along the curve.

Recommended for smooth presentation:
    python xdi_to_dynamic_gif.py sample.xdi --speed-mode x --frames 240 --frame-duration 0.05 --hold-frames 20

If the vertical edge still looks too fast, use:
    python xdi_to_dynamic_gif.py sample.xdi --speed-mode arc --frames 260 --frame-duration 0.05 --hold-frames 20
"""

from __future__ import annotations

import argparse
from pathlib import Path
import imageio.v2 as imageio
import matplotlib.pyplot as plt
import numpy as np


DEFAULT_XLABEL = "Energy (eV)"
DEFAULT_YLABEL = "Absorption (a.u.)"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a dynamic GIF from an XDI spectrum."
    )

    parser.add_argument("input_file", help="Path to the .xdi file")

    parser.add_argument(
        "--output",
        help="Output GIF path. Default: same folder/same stem + .gif",
        default=None,
    )

    parser.add_argument(
        "--preview",
        help="Optional preview PNG path. Default: same folder/same stem + _preview.png",
        default=None,
    )

    parser.add_argument(
        "--x-col",
        type=int,
        default=1,
        help="1-based numeric column index for x values. Default: 1.",
    )

    parser.add_argument(
        "--y-col",
        type=int,
        default=2,
        help="1-based numeric column index for y values. Default: 2.",
    )

    parser.add_argument(
        "--title",
        default=None,
        help="Custom plot title. Default: input file stem.",
    )

    parser.add_argument(
        "--xlabel",
        default=DEFAULT_XLABEL,
        help=f"X axis label. Default: {DEFAULT_XLABEL}.",
    )

    parser.add_argument(
        "--ylabel",
        default=DEFAULT_YLABEL,
        help=f"Y axis label. Default: {DEFAULT_YLABEL}.",
    )

    parser.add_argument(
        "--use-xdi-labels",
        action="store_true",
        help=(
            "Use axis labels inferred from XDI column metadata when available. "
            "By default, generic labels are used."
        ),
    )

    parser.add_argument(
        "--speed-mode",
        choices=["index", "x", "arc"],
        default="index",
        help=(
            "Animation speed mode. "
            "'index' advances by data rows, 'x' advances uniformly along x, "
            "'arc' advances uniformly along the visual curve. Default: index."
        ),
    )

    parser.add_argument(
        "--frames",
        type=int,
        default=240,
        help=(
            "Number of reveal frames for speed-mode x or arc. "
            "Higher values make the GIF longer/slower. Default: 240."
        ),
    )

    parser.add_argument(
        "--step",
        type=int,
        default=1,
        help=(
            "Default number of data points advanced per frame in speed-mode index. "
            "Default: 1."
        ),
    )

    parser.add_argument(
        "--step-before",
        type=int,
        default=None,
        help=(
            "Number of data points advanced per frame before --switch-x "
            "in speed-mode index. If omitted, uses --step."
        ),
    )

    parser.add_argument(
        "--step-after",
        type=int,
        default=None,
        help=(
            "Number of data points advanced per frame after --switch-x "
            "in speed-mode index. If omitted, uses --step."
        ),
    )

    parser.add_argument(
        "--switch-x",
        type=float,
        default=None,
        help=(
            "X value where the animation speed changes in speed-mode index. "
            "Example: absorption edge energy."
        ),
    )

    parser.add_argument(
        "--hold-frames",
        type=int,
        default=20,
        help="Number of extra frames to hold at the end. Default: 20.",
    )

    parser.add_argument(
        "--frame-duration",
        type=float,
        default=0.04,
        help="Duration of each GIF frame in seconds. Default: 0.04.",
    )

    parser.add_argument(
        "--marker-size",
        type=float,
        default=28.0,
        help="Size of the moving point marker. Default: 28.",
    )

    parser.add_argument(
        "--line-width",
        type=float,
        default=2.0,
        help="Line width. Default: 2.0.",
    )

    parser.add_argument(
        "--dpi",
        type=int,
        default=120,
        help="Figure DPI for rendered frames. Default: 120.",
    )

    parser.add_argument(
        "--width",
        type=float,
        default=10.0,
        help="Figure width in inches. Default: 10.",
    )

    parser.add_argument(
        "--height",
        type=float,
        default=7.0,
        help="Figure height in inches. Default: 7.",
    )

    return parser.parse_args()


def read_xdi_numeric_table(path: Path) -> tuple[np.ndarray, list[str]]:
    rows: list[list[float]] = []
    header_lines: list[str] = []

    with path.open("r", encoding="utf-8", errors="replace") as f:
        for raw_line in f:
            line = raw_line.strip()

            if not line:
                continue

            if line.startswith("#"):
                header_lines.append(line)
                continue

            parts = line.split()

            try:
                row = [float(value) for value in parts]
            except ValueError:
                continue

            rows.append(row)

    if not rows:
        raise ValueError("No numeric data rows were found in the XDI file.")

    max_len = max(len(row) for row in rows)

    normalized_rows = []
    for row in rows:
        if len(row) < max_len:
            row = row + [np.nan] * (max_len - len(row))
        normalized_rows.append(row)

    return np.array(normalized_rows, dtype=float), header_lines


def infer_axis_labels(
    header_lines: list[str],
    x_col_1based: int,
    y_col_1based: int,
) -> tuple[str | None, str | None]:
    x_label = None
    y_label = None

    x_key = f"# Column.{x_col_1based}:"
    y_key = f"# Column.{y_col_1based}:"

    for line in header_lines:
        if line.startswith(x_key):
            x_label = " ".join(line.replace(x_key, "", 1).split())

        if line.startswith(y_key):
            y_label = " ".join(line.replace(y_key, "", 1).split())

    return x_label, y_label


def build_index_frame_targets(
    x: np.ndarray,
    step: int,
    step_before: int | None,
    step_after: int | None,
    switch_x: float | None,
) -> list[float]:
    """
    Build frame targets in terms of floating point data index.

    This is the original mode: the animation progresses by data rows.
    """
    default_step = max(1, step)

    step_before_value = (
        max(1, step_before) if step_before is not None else default_step
    )

    step_after_value = max(1, step_after) if step_after is not None else default_step

    if switch_x is None:
        indices = list(range(0, len(x), default_step))

    else:
        split_idx = int(np.searchsorted(x, switch_x, side="left"))

        before_indices = list(
            range(
                0,
                max(1, split_idx),
                step_before_value,
            )
        )

        after_indices = list(
            range(
                max(0, split_idx),
                len(x),
                step_after_value,
            )
        )

        indices = before_indices + after_indices

    indices = sorted(set(index for index in indices if 0 <= index < len(x)))

    if not indices or indices[-1] != len(x) - 1:
        indices.append(len(x) - 1)

    return [float(index) for index in indices]


def build_x_frame_targets(x: np.ndarray, frames: int) -> list[float]:
    """
    Build frame targets with approximately constant speed along x.

    The returned values are floating point data indices obtained by
    interpolating equally spaced x positions back into the data index.
    """
    n_frames = max(2, frames)

    x_targets = np.linspace(x[0], x[-1], n_frames)
    data_indices = np.arange(len(x), dtype=float)

    return list(np.interp(x_targets, x, data_indices))


def build_arc_frame_targets(x: np.ndarray, y: np.ndarray, frames: int) -> list[float]:
    """
    Build frame targets with approximately constant visual speed along the curve.

    The path length is computed in normalized x/y coordinates so that the
    chosen frames are spaced approximately uniformly in the displayed plot.
    """
    n_frames = max(2, frames)

    x_span = np.max(x) - np.min(x)
    y_span = np.max(y) - np.min(y)

    if x_span == 0:
        x_span = 1.0
    if y_span == 0:
        y_span = 1.0

    x_norm = (x - np.min(x)) / x_span
    y_norm = (y - np.min(y)) / y_span

    dx = np.diff(x_norm)
    dy = np.diff(y_norm)
    segment_lengths = np.sqrt(dx**2 + dy**2)

    cumulative = np.concatenate([[0.0], np.cumsum(segment_lengths)])

    if cumulative[-1] == 0:
        return list(np.linspace(0, len(x) - 1, n_frames))

    arc_targets = np.linspace(0.0, cumulative[-1], n_frames)
    data_indices = np.arange(len(x), dtype=float)

    return list(np.interp(arc_targets, cumulative, data_indices))


def interpolate_curve_at_index(
    x: np.ndarray,
    y: np.ndarray,
    index_float: float,
) -> tuple[np.ndarray, np.ndarray, float, float]:
    """
    Return the curve revealed up to a floating point index.

    If index_float is between two data points, the current point is
    linearly interpolated.
    """
    index_float = max(0.0, min(float(index_float), float(len(x) - 1)))

    i0 = int(np.floor(index_float))
    i1 = min(i0 + 1, len(x) - 1)
    frac = index_float - i0

    x_current = x[i0] * (1.0 - frac) + x[i1] * frac
    y_current = y[i0] * (1.0 - frac) + y[i1] * frac

    x_history = x[: i0 + 1]
    y_history = y[: i0 + 1]

    if i1 != i0 and (x_history[-1] != x_current or y_history[-1] != y_current):
        x_plot = np.append(x_history, x_current)
        y_plot = np.append(y_history, y_current)
    else:
        x_plot = x_history
        y_plot = y_history

    return x_plot, y_plot, x_current, y_current


def make_animation(
    x: np.ndarray,
    y: np.ndarray,
    title: str,
    xlabel: str,
    ylabel: str,
    speed_mode: str,
    frames: int,
    step: int,
    step_before: int | None,
    step_after: int | None,
    switch_x: float | None,
    hold_frames: int,
    frame_duration: float,
    marker_size: float,
    line_width: float,
    dpi: int,
    fig_width: float,
    fig_height: float,
    gif_path: Path,
    preview_path: Path,
) -> None:
    valid = np.isfinite(x) & np.isfinite(y)
    x = x[valid]
    y = y[valid]

    if x.size < 2:
        raise ValueError("Not enough valid points to build the animation.")

    # Sorting by x makes speed-mode x robust for normal absorption spectra.
    order = np.argsort(x)
    x = x[order]
    y = y[order]

    x_min, x_max = np.min(x), np.max(x)
    y_min, y_max = np.min(y), np.max(y)

    x_pad = 0.03 * (x_max - x_min if x_max != x_min else 1.0)
    y_pad = 0.08 * (y_max - y_min if y_max != y_min else 1.0)

    if speed_mode == "index":
        frame_targets = build_index_frame_targets(
            x=x,
            step=step,
            step_before=step_before,
            step_after=step_after,
            switch_x=switch_x,
        )
    elif speed_mode == "x":
        frame_targets = build_x_frame_targets(x=x, frames=frames)
    elif speed_mode == "arc":
        frame_targets = build_arc_frame_targets(x=x, y=y, frames=frames)
    else:
        raise ValueError(f"Unknown speed mode: {speed_mode}")

    fig, ax = plt.subplots(figsize=(fig_width, fig_height), dpi=dpi)

    line, = ax.plot([], [], linewidth=line_width)
    point = ax.scatter([], [], s=marker_size, zorder=3)

    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)

    ax.set_xlim(x_min - x_pad, x_max + x_pad)
    ax.set_ylim(y_min - y_pad, y_max + y_pad)

    ax.grid(True, alpha=0.35)
    fig.tight_layout()

    frames_buffer = []

    for index_float in frame_targets:
        x_plot, y_plot, x_current, y_current = interpolate_curve_at_index(
            x=x,
            y=y,
            index_float=index_float,
        )

        line.set_data(x_plot, y_plot)
        point.set_offsets([[x_current, y_current]])

        fig.canvas.draw()
        frame = np.asarray(fig.canvas.buffer_rgba())[:, :, :3].copy()
        frames_buffer.append(frame)

    for _ in range(max(0, hold_frames)):
        frames_buffer.append(frames_buffer[-1].copy())

    imageio.mimsave(
        gif_path,
        frames_buffer,
        duration=frame_duration,
        loop=0,
    )

    line.set_data(x, y)
    point.set_offsets([[x[-1], y[-1]]])
    fig.canvas.draw()
    fig.savefig(preview_path)

    plt.close(fig)


def main() -> None:
    args = parse_args()

    input_path = Path(args.input_file).expanduser().resolve()

    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    gif_path = (
        Path(args.output).expanduser().resolve()
        if args.output
        else input_path.with_suffix(".gif")
    )

    preview_path = (
        Path(args.preview).expanduser().resolve()
        if args.preview
        else input_path.with_name(f"{input_path.stem}_preview.png")
    )

    data, header_lines = read_xdi_numeric_table(input_path)

    x_idx = args.x_col - 1
    y_idx = args.y_col - 1

    if x_idx < 0 or y_idx < 0:
        raise ValueError("Column indices must be 1 or greater.")

    if x_idx >= data.shape[1] or y_idx >= data.shape[1]:
        raise ValueError(
            f"Requested columns exceed available numeric columns "
            f"({data.shape[1]} total)."
        )

    x = data[:, x_idx]
    y = data[:, y_idx]

    inferred_x, inferred_y = infer_axis_labels(
        header_lines=header_lines,
        x_col_1based=args.x_col,
        y_col_1based=args.y_col,
    )

    title = args.title if args.title else input_path.stem

    if args.use_xdi_labels:
        xlabel = inferred_x if inferred_x is not None else args.xlabel
        ylabel = inferred_y if inferred_y is not None else args.ylabel
    else:
        xlabel = args.xlabel
        ylabel = args.ylabel

    make_animation(
        x=x,
        y=y,
        title=title,
        xlabel=xlabel,
        ylabel=ylabel,
        speed_mode=args.speed_mode,
        frames=args.frames,
        step=args.step,
        step_before=args.step_before,
        step_after=args.step_after,
        switch_x=args.switch_x,
        hold_frames=args.hold_frames,
        frame_duration=args.frame_duration,
        marker_size=args.marker_size,
        line_width=args.line_width,
        dpi=args.dpi,
        fig_width=args.width,
        fig_height=args.height,
        gif_path=gif_path,
        preview_path=preview_path,
    )

    print(f"GIF saved to: {gif_path}")
    print(f"Preview PNG saved to: {preview_path}")


if __name__ == "__main__":
    main()
