# ================================================================
# GRID SWEEP SAMPLER
# ----------------------------------------------------------------
# Creates every combination of parameter values on a regular grid,
# then steps through them one at a time. Think of it like nested
# for-loops: variable 0 changes fastest (ones digit on an odometer),
# variable 1 next, and so on.
#
# HOW IT WORKS
#   1. Build a linspace axis for each variable (start -> end, N points)
#   2. Combine axes into a full grid (total samples = N0 x N1 x ...)
#   3. Each Trigger pulse (Run) advances to the next grid point
#   4. Current X values are stored in sc.sticky["sampler_x"] so
#      the Logger can pair them with the analysis result Y
#
# INPUTS
#   XNames  (list[str])   - Variable names (auto x_00, x_01 ... if empty)
#   XStarts (list[float]) - Start value for each variable
#   XEnds   (list[float]) - End value for each variable
#   XNs     (list[int])   - Number of samples per variable
#   Run     (bool)        - Trigger pulse to advance one step
#   Reset   (bool)        - Reset sweep back to the first sample
#
# OUTPUTS
#   XVals   (list[float]) - Current sample values
#   Index   (int)         - Current sample index (wire to Logger)
#   Done    (bool)        - True after the last sample has been reached
#
# Ozguc Bertug Capunaman - CMDO - Spring 2026
# ================================================================

import scriptcontext as sc


# --- Helpers ---------------------------------------------------------

def as_list(v):
    """Ensure v is a plain Python list (handles None, scalars, tuples)."""
    if v is None:
        return []
    return list(v) if isinstance(v, (list, tuple)) else [v]


def linspace(a, b, n):
    """Return n evenly spaced values from a to b (inclusive on both ends)."""
    a, b, n = float(a), float(b), max(1, int(n))
    if n == 1:
        return [a]
    step = (b - a) / (n - 1)
    vals = [a + i * step for i in range(n)]
    vals[-1] = b  # Snap the last value to avoid floating-point drift
    return vals


def prod(ints):
    """Product of a list of integers (total number of grid points)."""
    out = 1
    for v in ints:
        out *= int(v)
    return out


def unravel(flat_idx, shape):
    """Convert a flat index into per-axis indices.

    Variable 0 ticks fastest - like the ones digit on an odometer.
    Example: shape [3, 2] cycles as (0,0),(1,0),(2,0),(0,1),(1,1),(2,1).
    """
    multi = []
    for dim in shape:
        multi.append(flat_idx % int(dim))
        flat_idx //= int(dim)
    return multi


# --- Normalize inputs ------------------------------------------------

x_starts = as_list(XStarts)
x_ends = as_list(XEnds)
x_ns = as_list(XNs)

assert len(x_starts) == len(x_ends) == len(x_ns), (
    "XStarts, XEnds, and XNs must all have the same length"
)

n = len(x_starts)

x_names = as_list(XNames)
if len(x_names) == 0:
    x_names = [f"x_{i:02d}" for i in range(n)]
else:
    assert len(x_names) == n, "XNames length must match XStarts/XEnds/XNs"

x_starts = [float(v) for v in x_starts]
x_ends = [float(v) for v in x_ends]
x_ns = [max(1, int(v)) for v in x_ns]


# --- Initialize / reset persistent state ----------------------------
# sc.sticky is Grasshopper's dictionary that persists between solves.
# sc.sticky["sampler_x"] is the bridge between Sampler and Logger.

state = sc.sticky.get("grid_sweep_state")
if state is None or Reset:
    state = {"axes": None, "shape": None, "index": 0, "done": False, "sig": None}

sig = (tuple(x_names), tuple(x_starts), tuple(x_ends), tuple(x_ns))
if state["axes"] is None or state["sig"] != sig:
    axes = [linspace(x_starts[i], x_ends[i], x_ns[i]) for i in range(n)]
    shape = [len(ax) for ax in axes]
    state.update({"axes": axes, "shape": shape, "index": 0, "done": False, "sig": sig})


# --- Default outputs -------------------------------------------------

axes = state["axes"]
shape = state["shape"]
idx = int(state["index"])
total = prod(shape) if shape else 0

if total == 0:
    XVals, Index, Done = [], 0, True
else:
    if idx >= total:
        idx = total - 1
        state["index"] = idx
        state["done"] = True

    mi = unravel(idx, shape)
    XVals = [float(axes[i][mi[i]]) for i in range(n)]
    Index = idx
    Done = bool(state["done"])

sc.sticky["sampler_x"] = {"names": x_names, "vals": XVals}
sc.sticky["grid_sweep_state"] = state


# --- Main logic ------------------------------------------------------
# Each Run=True pulse moves to the next grid point.

if Run and not state["done"] and total > 0:
    nxt = idx + 1
    if nxt >= total:
        state["done"] = True
        state["index"] = total - 1
    else:
        state["index"] = nxt

Done = bool(state["done"])
sc.sticky["grid_sweep_state"] = state
