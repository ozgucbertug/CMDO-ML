# ================================================================
# IMAGE DATA LOGGER
# ----------------------------------------------------------------
# Writes a grayscale image array to disk as a PNG - one image per
# sample. This is the file-writing companion to encoder_imageData.py.
#
# HOW IT WORKS
#   1. Receive a 2D grayscale ImageArray from the encoder
#   2. Check that the array is rectangular and contains pixel values
#   3. Write those values into a bitmap
#   4. Save the bitmap as <Index>.png
#
# INPUTS
#   ImageArray (list[list[int]]) - 2D grayscale array from the encoder
#   Directory  (str)             - Output folder for the PNG files
#   Index      (int)             - Sample index (wire from Sampler)
#   Run        (bool)            - Trigger pulse to write one image
#   Reset      (bool)            - Allow re-writing the same Index
#
# OUTPUTS
#   PathOut    (str)             - Full path of the written PNG
#   Status     (str)             - Human-readable status message
#
# Ozguc Bertug Capunaman - CMDO - Spring 2026
# ================================================================

import os

import scriptcontext as sc
from System.Drawing import Bitmap, Color
from System.Drawing.Imaging import ImageFormat


# --- Helpers ---------------------------------------------------------

def as_list(v):
    """Ensure v is a plain Python list (handles None, scalars, tuples)."""
    if v is None:
        return []
    if isinstance(v, (list, tuple)):
        return list(v)
    try:
        return list(v)
    except TypeError:
        return [v]


# --- Initialize / reset persistent state ----------------------------

sticky_key = "heightmap_logger_state"
if "ghenv" in globals():
    sticky_key += "_{}".format(ghenv.Component.InstanceGuid)

state = sc.sticky.get(sticky_key)
if state is None or Reset:
    state = {"last_index": None}


# --- Normalize inputs ------------------------------------------------

ok = True
index_int = None
directory = ""
image_rows = []
height = 0
width = 0
status = ""

if not Run:
    status = "Idle (Run is False)"
    ok = False

if ok and Index is None:
    status = "Index is None"
    ok = False

if ok:
    try:
        index_int = int(Index)
    except (TypeError, ValueError):
        status = "Index must be an integer"
        ok = False

if ok and state["last_index"] == index_int:
    status = "Index unchanged - nothing written"
    ok = False

if ok:
    directory = (Directory or "").strip()
    if not directory:
        status = "Directory is empty"
        ok = False

if ok:
    image_rows = [as_list(row) for row in as_list(ImageArray)]
    if not image_rows:
        status = "ImageArray is empty"
        ok = False

if ok:
    try:
        height = len(image_rows)
        width = len(image_rows[0])
        if height <= 0 or width <= 0:
            raise ValueError
        for row in image_rows:
            if len(row) != width:
                raise ValueError
    except Exception:
        status = "ImageArray must be a rectangular 2D list"
        ok = False


# --- Default outputs -------------------------------------------------

PathOut = ""
Status = status


# --- Main logic ------------------------------------------------------

if ok:
    directory = os.path.normpath(os.path.expandvars(directory))
    os.makedirs(directory, exist_ok=True)

    bmp = Bitmap(width, height)

    for row in range(height):
        for col in range(width):
            try:
                g = int(round(float(image_rows[row][col])))
            except (TypeError, ValueError):
                g = 0
            g = max(0, min(255, g))
            bmp.SetPixel(col, row, Color.FromArgb(g, g, g))

    out_path = os.path.join(directory, f"{index_int:06d}.png")
    bmp.Save(out_path, ImageFormat.Png)
    bmp.Dispose()

    PathOut = out_path
    Status = "Wrote heightmap: " + out_path
    state["last_index"] = index_int

sc.sticky[sticky_key] = state
print("Status: ", Status)
