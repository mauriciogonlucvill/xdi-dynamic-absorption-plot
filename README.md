# Dynamic XAS Absorption GIF from XDI Files

This repository contains a Python script for generating animated absorption plots from `.xdi` files.

The script reads the numerical table inside an XDI file, extracts an energy axis and an absorption-related signal, and creates a GIF in which the curve is progressively drawn. It is intended for scientific visualization, presentations, educational material, and outreach activities related to X-ray absorption spectroscopy.

## What the script does

The script:

1. Reads an `.xdi` file.
2. Ignores header and comment lines starting with `#`.
3. Extracts numerical columns from the data table.
4. Uses one column as the x-axis, usually energy.
5. Uses another column as the y-axis, usually an absorption-related signal.
6. Sorts the data by the x-axis.
7. Generates a progressive animation of the curve.
8. Saves a looping `.gif`.
9. Saves a final static preview image as `.png`.

By default, the script uses generic axis labels:

```text
Energy (eV)
Absorption (a.u.)
```

If desired, it can also use labels inferred from XDI column metadata.

## Repository contents

Recommended repository structure:

```text
.
├── xdi_to_dynamic_gif.py
├── README.md
├── requirements.txt
├── .gitignore
└── LICENSE
```

This repository does not include experimental data. Users should only process and publish data that they are authorized to share.

## Requirements

The script requires:

```text
Python >= 3.10
numpy
matplotlib
imageio
pillow
```

A recommended `requirements.txt` file is:

```text
numpy
matplotlib
imageio
pillow
```

## Installation

### Windows PowerShell

Open PowerShell inside the repository folder.

Create a virtual environment:

```powershell
py -3 -m venv .venv
```

Activate the environment:

```powershell
.\.venv\Scripts\Activate.ps1
```

Update `pip`:

```powershell
python -m pip install --upgrade pip
```

Install the dependencies:

```powershell
pip install -r requirements.txt
```

If PowerShell blocks the activation script, you can either allow local scripts:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

or run Python directly from the virtual environment without activating it:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### Linux

Open a terminal inside the repository folder.

Create a virtual environment:

```bash
python3 -m venv .venv
```

Activate the environment:

```bash
source .venv/bin/activate
```

Update `pip`:

```bash
python -m pip install --upgrade pip
```

Install the dependencies:

```bash
pip install -r requirements.txt
```

## Basic usage

### Windows PowerShell

```powershell
python .\xdi_to_dynamic_gif.py .\sample.xdi
```

### Linux

```bash
python xdi_to_dynamic_gif.py sample.xdi
```

By default, the script creates two files in the same folder as the input file:

```text
sample.gif
sample_preview.png
```

The GIF contains the animated curve, and the PNG contains the final static preview.

## Input format

The script is designed for `.xdi` files containing a numerical data table.

Header or metadata lines should start with:

```text
#
```

Numerical rows should contain whitespace-separated values, for example:

```text
11500.0 0.123
11501.0 0.125
11502.0 0.130
```

By default:

```text
--x-col 1
--y-col 2
```

That means the first numerical column is used as the x-axis and the second numerical column is used as the y-axis.

If your file has a different column structure, choose the desired columns manually.

Example:

```bash
python xdi_to_dynamic_gif.py sample.xdi --x-col 1 --y-col 4
```

## Axis labels

By default, the script uses generic labels:

```text
Energy (eV)
Absorption (a.u.)
```

Example:

```bash
python xdi_to_dynamic_gif.py sample.xdi
```

If the XDI file contains column metadata and you want to use those original labels, run:

```bash
python xdi_to_dynamic_gif.py sample.xdi --use-xdi-labels
```

For example, this may use labels such as:

```text
energy eV
mutrans arbitrary
```

You can also define custom labels manually:

```bash
python xdi_to_dynamic_gif.py sample.xdi --xlabel "Energy (eV)" --ylabel "Normalized absorption (a.u.)"
```

## Custom output paths

You can choose the output GIF and preview PNG paths.

### Windows PowerShell

```powershell
python .\xdi_to_dynamic_gif.py .\sample.xdi --output .\output\curve.gif --preview .\output\curve_preview.png
```

### Linux

```bash
python xdi_to_dynamic_gif.py sample.xdi --output output/curve.gif --preview output/curve_preview.png
```

If a path contains spaces, use quotes.

Example:

```bash
python xdi_to_dynamic_gif.py "data/sample spectrum.xdi"
```

## Animation speed modes

The script has three speed modes:

```text
index
x
arc
```

### 1. `index` mode

This is the default mode.

The animation advances by data row number. The main parameter is:

```text
--step
```

A larger `--step` value makes the curve advance faster because more data points are skipped per frame.

Example:

```bash
python xdi_to_dynamic_gif.py sample.xdi --speed-mode index --step 5
```

Faster version:

```bash
python xdi_to_dynamic_gif.py sample.xdi --speed-mode index --step 10 --frame-duration 0.025 --hold-frames 8
```

You can also use different speeds before and after a given x value:

```bash
python xdi_to_dynamic_gif.py sample.xdi --speed-mode index --step-before 10 --step-after 3 --switch-x 11580
```

This can be useful when you want the animation to change speed near an absorption edge.

### 2. `x` mode

This mode advances with approximately constant speed along the x-axis.

The main parameter is:

```text
--frames
```

More frames make the animation smoother and slower. Fewer frames make it faster and lighter.

Recommended smooth version:

```bash
python xdi_to_dynamic_gif.py sample.xdi --speed-mode x --frames 240 --frame-duration 0.05 --hold-frames 20
```

Faster version:

```bash
python xdi_to_dynamic_gif.py sample.xdi --speed-mode x --frames 120 --frame-duration 0.03 --hold-frames 10
```

Very fast test version:

```bash
python xdi_to_dynamic_gif.py sample.xdi --speed-mode x --frames 80 --frame-duration 0.02 --hold-frames 5
```

### 3. `arc` mode

This mode advances with approximately constant visual speed along the curve.

It is useful when the curve has a steep absorption edge or regions where the visual motion feels too fast or too slow.

Recommended version:

```bash
python xdi_to_dynamic_gif.py sample.xdi --speed-mode arc --frames 160 --frame-duration 0.03 --hold-frames 10
```

Smoother version:

```bash
python xdi_to_dynamic_gif.py sample.xdi --speed-mode arc --frames 260 --frame-duration 0.05 --hold-frames 20
```

Faster version:

```bash
python xdi_to_dynamic_gif.py sample.xdi --speed-mode arc --frames 90 --frame-duration 0.025 --hold-frames 8
```

## Recommended commands

### Balanced command for presentations

```bash
python xdi_to_dynamic_gif.py sample.xdi --speed-mode arc --frames 120 --frame-duration 0.03 --hold-frames 10
```

### Faster generation and smaller file

```bash
python xdi_to_dynamic_gif.py sample.xdi --speed-mode x --frames 100 --frame-duration 0.025 --hold-frames 8 --dpi 90 --width 8 --height 5
```

### High-quality version

```bash
python xdi_to_dynamic_gif.py sample.xdi --speed-mode arc --frames 240 --frame-duration 0.04 --hold-frames 20 --dpi 150 --width 10 --height 7
```

## Main parameters

| Parameter          | Meaning                                                    |
| ------------------ | ---------------------------------------------------------- |
| `input_file`       | Path to the `.xdi` file.                                   |
| `--output`         | Output GIF path.                                           |
| `--preview`        | Output preview PNG path.                                   |
| `--x-col`          | 1-based column index for x values. Default: `1`.           |
| `--y-col`          | 1-based column index for y values. Default: `2`.           |
| `--title`          | Custom plot title. Default: input file name.               |
| `--xlabel`         | Custom x-axis label.                                       |
| `--ylabel`         | Custom y-axis label.                                       |
| `--use-xdi-labels` | Use labels inferred from XDI column metadata.              |
| `--speed-mode`     | Animation mode: `index`, `x`, or `arc`.                    |
| `--frames`         | Number of reveal frames for `x` or `arc` mode.             |
| `--step`           | Number of data points advanced per frame in `index` mode.  |
| `--step-before`    | Step size before `--switch-x` in `index` mode.             |
| `--step-after`     | Step size after `--switch-x` in `index` mode.              |
| `--switch-x`       | x value where the animation speed changes in `index` mode. |
| `--hold-frames`    | Number of extra frames to hold the final curve.            |
| `--frame-duration` | Duration of each GIF frame in seconds.                     |
| `--marker-size`    | Size of the moving point marker.                           |
| `--line-width`     | Width of the plotted curve.                                |
| `--dpi`            | Figure resolution.                                         |
| `--width`          | Figure width in inches.                                    |
| `--height`         | Figure height in inches.                                   |

## How to make the GIF faster

To make the animation itself faster:

```bash
--frame-duration 0.02
```

To reduce the total number of frames:

```bash
--frames 100
```

To make the file smaller and faster to generate:

```bash
--dpi 90 --width 8 --height 5
```

Example:

```bash
python xdi_to_dynamic_gif.py sample.xdi --speed-mode arc --frames 90 --frame-duration 0.025 --hold-frames 8 --dpi 90 --width 8 --height 5
```

## How to make the GIF smoother

Use more frames and a slightly larger frame duration:

```bash
python xdi_to_dynamic_gif.py sample.xdi --speed-mode arc --frames 260 --frame-duration 0.05 --hold-frames 20
```

This produces a smoother animation but also increases file size and generation time.

## Troubleshooting

### `ModuleNotFoundError`

If you see an error such as:

```text
ModuleNotFoundError: No module named 'imageio'
```

install the dependencies:

```bash
pip install -r requirements.txt
```

### PowerShell does not activate the virtual environment

If this command fails:

```powershell
.\.venv\Scripts\Activate.ps1
```

you can either change the execution policy:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

or run Python directly:

```powershell
.\.venv\Scripts\python.exe .\xdi_to_dynamic_gif.py .\sample.xdi
```

### No numeric data rows found

This means the script did not find a numerical table in the input file.

Check that the file contains numerical rows and that they are not commented with `#`.

### Requested columns exceed available numeric columns

This means the selected `--x-col` or `--y-col` does not exist in the numerical table.

For example, if the file has only two numerical columns, this will fail:

```bash
python xdi_to_dynamic_gif.py sample.xdi --y-col 4
```

Use a valid column number instead:

```bash
python xdi_to_dynamic_gif.py sample.xdi --x-col 1 --y-col 2
```

### The GIF is too slow

Use fewer frames or smaller frame duration:

```bash
python xdi_to_dynamic_gif.py sample.xdi --speed-mode arc --frames 90 --frame-duration 0.025
```

### The GIF file is too large

Reduce frames, DPI, width, or height:

```bash
python xdi_to_dynamic_gif.py sample.xdi --frames 100 --dpi 90 --width 8 --height 5
```

### The y-axis shows labels like `mutrans arbitrary`

This happens if `--use-xdi-labels` is enabled and the XDI file contains that label.

To use generic labels, do not pass `--use-xdi-labels`:

```bash
python xdi_to_dynamic_gif.py sample.xdi
```

Or set a custom label manually:

```bash
python xdi_to_dynamic_gif.py sample.xdi --ylabel "Absorption (a.u.)"
```

## Data and privacy note

This repository should not include experimental data unless the user has permission to share it.

Recommended `.gitignore` additions:

```gitignore
# Experimental input data
*.xdi
*.dat
*.csv

# Generated visual outputs
*.gif
*.png
*.jpg
*.jpeg
*.svg
*.pdf

# Generated output folders
output/
outputs/
figures/
plots/
animations/
previews/
results/
```

This helps avoid accidentally uploading experimental files or generated outputs.

## License

This project is distributed under the MIT License.
