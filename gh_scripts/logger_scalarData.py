# ================================================================
# SCALAR DATA LOGGER
# ----------------------------------------------------------------
# Collects each sample's X values (from the Sampler) and Y values
# (from your Grasshopper analysis) into a single CSV file - one row
# per sample. This CSV is the dataset you will later load for ML.
#
# HOW IT WORKS
#   1. The Sampler stores X in sc.sticky["sampler_x"]
#   2. This Logger reads that X, pairs it with the Y you provide,
#      and appends one row to the CSV
#   3. After Reset, the first write overwrites the old file (mode="w");
#      every write after that appends a new row (mode="a")
#
# INPUTS
#   Index     (int)        - Current sample index (wire from Sampler)
#   Ys        (list/value) - Analysis outputs for this sample
#   YNames    (list[str])  - Column names for Ys (auto y_00, y_01 ... if wrong length)
#   Directory (str)        - Folder to save the CSV in
#   FileName  (str)        - CSV file name (default "dataset.csv")
#   Run       (bool)       - Trigger pulse to log one row
#   Reset     (bool)       - Clear state so next write starts a fresh file
#
# OUTPUTS
#   Count     (int)        - Number of rows written since last Reset
#   LastIndex (int/None)   - Index of the most recently written row
#   LastRow   (dict)       - Contents of the most recently written row
#
# Ozguc Bertug Capunaman - CMDO - Spring 2026
# ================================================================

import csv
import os

import scriptcontext as sc


# --- Helpers ---------------------------------------------------------

def as_list(v):
    """Ensure v is a plain Python list (handles None, scalars, .NET arrays)."""
    if v is None:
        return []
    if isinstance(v, (list, tuple)):
        return list(v)
    try:
        return list(v)  # Handles .NET IEnumerable / System.Array
    except TypeError:
        return [v]


# --- Initialize / reset persistent state ----------------------------

state = sc.sticky.get("scalar_logger_state")
if state is None or Reset:
    state = {"last_index": None, "overwrite": True, "count": 0}


# --- Normalize inputs ------------------------------------------------

x_info = sc.sticky.get("sampler_x", {})
x_names = x_info.get("names", [])
x_vals = x_info.get("vals", [])

y_vals = as_list(Ys)
y_names = as_list(YNames)
if len(y_names) != len(y_vals):
    y_names = [f"y_{i:02d}" for i in range(len(y_vals))]


# --- Build CSV path --------------------------------------------------

directory = (Directory or "").strip()
file_name = (FileName or "dataset.csv").strip()
if not file_name.lower().endswith(".csv"):
    file_name += ".csv"

csv_path = ""
if directory:
    os.makedirs(directory, exist_ok=True)
    csv_path = os.path.join(directory, file_name)


# --- Default outputs -------------------------------------------------

LastRow = {}
LastIndex = state["last_index"]
Count = state["count"]


# --- Main logic ------------------------------------------------------
# All conditions must be true to write:
#   - Run is True (trigger pulse fired)
#   - Index is not None (Sampler is active)
#   - Index differs from last written (avoid duplicate rows)
#   - Sampler has written X values to sc.sticky["sampler_x"]

should_log = (
    bool(Run)
    and Index is not None
    and Index != state["last_index"]
    and len(x_names) > 0
    and bool(csv_path)
)

if should_log:
    # Row order: index, then X columns (sampler order), then Y columns
    header = ["index"] + x_names + y_names
    row = dict(zip(header, [int(Index)] + x_vals + y_vals))

    mode = "w" if state["overwrite"] else "a"
    file_exists = os.path.exists(csv_path)

    with open(csv_path, mode, newline="") as f:
        writer = csv.DictWriter(f, fieldnames=header, extrasaction="ignore")
        if mode == "w" or not file_exists:
            writer.writeheader()
        writer.writerow(row)

    LastRow = row
    LastIndex = int(Index)
    Count = state["count"] + 1

    state.update({"last_index": LastIndex, "overwrite": False, "count": Count})

sc.sticky["scalar_logger_state"] = state
