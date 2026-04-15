# ================================================================
# RANDOM UNIFORM SAMPLER
# ----------------------------------------------------------------
# Generates N random samples where each variable is drawn uniformly
# between its start and end value. A fixed seed makes the results
# reproducible - the same seed always produces the same samples.
#
# HOW IT WORKS
#   1. Generate all N samples up-front using the given Seed
#   2. Each Trigger pulse (Run) advances to the next sample
#   3. Current X values are stored in sc.sticky["sampler_x"] so
#      the Logger can pair them with the analysis result Y
#
# INPUTS
#   XNames   (list[str])   - Variable names (auto x_00, x_01 ... if empty)
#   XStarts  (list[float]) - Lower bound for each variable
#   XEnds    (list[float]) - Upper bound for each variable
#   NSamples (int)         - Total number of random samples to generate
#   Seed     (int)         - Random seed for reproducibility
#   Run      (bool)        - Trigger pulse to advance one step
#   Reset    (bool)        - Reset back to first sample (re-generates from same Seed)
#
# OUTPUTS
#   XVals    (list[float]) - Current sample values
#   Index    (int)         - Current sample index (wire to Logger)
#   Done     (bool)        - True after the last sample has been reached
#
# Ozguc Bertug Capunaman - CMDO - Spring 2026
# ================================================================

import random

import scriptcontext as sc


# --- Helpers ---------------------------------------------------------

def as_list(v):
    """Ensure v is a plain Python list (handles None, scalars, tuples)."""
    if v is None:
        return []
    return list(v) if isinstance(v, (list, tuple)) else [v]


# --- Normalize inputs ------------------------------------------------

x_starts = as_list(XStarts)
x_ends = as_list(XEnds)

assert len(x_starts) == len(x_ends), "XStarts and XEnds must have the same length"

n = len(x_starts)

x_names = as_list(XNames)
if len(x_names) == 0:
    x_names = [f"x_{i:02d}" for i in range(n)]
else:
    assert len(x_names) == n, "XNames length must match XStarts/XEnds"

x_starts = [float(v) for v in x_starts]
x_ends = [float(v) for v in x_ends]
n_samples = max(0, int(NSamples or 0))
seed = int(Seed or 0)


# --- Initialize / reset persistent state ----------------------------
# sc.sticky is Grasshopper's dictionary that persists between solves.
# sc.sticky["sampler_x"] is the bridge between Sampler and Logger.

state = sc.sticky.get("random_sampler_state")
if state is None or Reset:
    state = {"samples": None, "index": 0, "done": False, "sig": None}

sig = (tuple(x_names), tuple(x_starts), tuple(x_ends), n_samples, seed)
if state["samples"] is None or state["sig"] != sig:
    rng = random.Random(seed)
    samples = [
        [rng.uniform(x_starts[j], x_ends[j]) for j in range(n)]
        for _ in range(n_samples)
    ]
    state.update({"samples": samples, "index": 0, "done": (n_samples == 0), "sig": sig})


# --- Default outputs -------------------------------------------------

samples = state["samples"]
idx = int(state["index"])

if n_samples == 0:
    XVals, Index, Done = [], 0, True
else:
    if idx >= n_samples:
        idx = n_samples - 1
        state["index"] = idx
        state["done"] = True

    XVals = [float(v) for v in samples[idx]]
    Index = idx
    Done = bool(state["done"])

sc.sticky["sampler_x"] = {"names": x_names, "vals": XVals}
sc.sticky["random_sampler_state"] = state


# --- Main logic ------------------------------------------------------
# Each Run=True pulse moves to the next random sample.

if Run and not state["done"] and n_samples > 0:
    nxt = idx + 1
    if nxt >= n_samples:
        state["done"] = True
        state["index"] = n_samples - 1
    else:
        state["index"] = nxt

Done = bool(state["done"])
sc.sticky["random_sampler_state"] = state
