# ================================================================
# GLOBAL + LOCAL FAMILY GRID SAMPLER
# ----------------------------------------------------------------
# Builds a family-structured sampling sequence for inverse-design
# data collection. Each global family emits:
#   1. One baseline sample with a zero local grid
#   2. Additional local variants sampled uniformly on an n x n grid
#
# The sampler stores the current structured case in sc.sticky so a
# paired logger component can write the dataset row without verbose
# Grasshopper wiring.
#
# INPUTS
#   GlobalNames     (list[str])   - Optional names for global vars
#   GlobalStarts    (list[float]) - Lower bound for each global var
#   GlobalEnds      (list[float]) - Upper bound for each global var
#   NGlobalFamilies (int)         - Number of global families
#   LocalGridN      (int)         - Local grid size n for an n x n grid
#   LocalStart      (float)       - Shared lower bound for all local cells
#   LocalEnd        (float)       - Shared upper bound for all local cells
#   NLocalVariants  (int)         - Total samples per family, including baseline
#   Seed            (int)         - Random seed for sampling
#   Run             (bool)        - Trigger pulse to advance one sample
#   Reset           (bool)        - Reset sampling back to the first sample
#
# OUTPUTS
#   SampleId        (int/None)        - Flat sample index
#   GlobalFamilyId  (int/None)        - 0-based family index
#   LocalVariantId  (int/None)        - -1 for baseline, else 0-based variant
#   GlobalVals      (list[float])     - Current global values
#   LocalGridVals   (list[float])     - Current local grid values (row-major)
#   Done            (bool)            - True after the final sample has been reached
#   Status          (str)             - Human-readable status message
#
# Ozguc Bertug Capunaman - CMDO - Spring 2026
# ================================================================

import random

import scriptcontext as sc


# --- Sticky keys ------------------------------------------------------

STICKY_PREFIX = "global_local_family"
ACTIVE_CASE_KEY = STICKY_PREFIX + "_active_case_key"

instance_suffix = ""
if "ghenv" in globals():
    instance_suffix = "_{}".format(ghenv.Component.InstanceGuid)

STATE_KEY = STICKY_PREFIX + "_state" + instance_suffix
CASE_KEY = STICKY_PREFIX + "_case" + instance_suffix


# --- Helpers ----------------------------------------------------------

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


def build_local_names(grid_n):
    """Return row-major local grid names."""
    width = max(2, len(str(max(0, grid_n - 1))))
    return [
        "l_r{row:0{w}d}_c{col:0{w}d}".format(row=row, col=col, w=width)
        for row in range(grid_n)
        for col in range(grid_n)
    ]


def build_case(state, flat_index):
    """Build one structured case dictionary from the current flat index."""
    samples_per_family = state["samples_per_family"]
    family_id = flat_index // samples_per_family
    sample_in_family = flat_index % samples_per_family
    local_variant_id = sample_in_family - 1

    global_vals = list(state["global_samples"][family_id])
    if local_variant_id < 0:
        local_flat_vals = [0.0] * state["local_cell_count"]
    else:
        local_flat_vals = list(state["local_variants"][family_id][local_variant_id])

    return {
        "sample_id": int(flat_index),
        "global_family_id": int(family_id),
        "local_variant_id": int(local_variant_id),
        "global": {
            "names": list(state["global_names"]),
            "vals": global_vals,
        },
        "local_grid": {
            "names": list(state["local_names"]),
            "vals": local_flat_vals,
        },
    }


# --- Normalize inputs -------------------------------------------------

ok = True
status = ""

global_starts = as_list(GlobalStarts)
global_ends = as_list(GlobalEnds)
global_names = [str(v).strip() for v in as_list(GlobalNames) if str(v).strip()]

if len(global_starts) != len(global_ends):
    ok = False
    status = "GlobalStarts and GlobalEnds must have the same length"

if ok:
    try:
        global_starts = [float(v) for v in global_starts]
        global_ends = [float(v) for v in global_ends]
        n_global_families = max(0, int(NGlobalFamilies or 0))
        local_grid_n = int(LocalGridN)
        local_start = float(LocalStart)
        local_end = float(LocalEnd)
        samples_per_family = max(0, int(NLocalVariants or 0))
        n_local_variants = max(0, samples_per_family - 1)
        seed = int(Seed or 0)
    except (TypeError, ValueError):
        ok = False
        status = "Numeric inputs are invalid"

if ok and local_grid_n < 1:
    ok = False
    status = "LocalGridN must be at least 1"

if ok and not (local_start <= 0.0 <= local_end):
    ok = False
    status = "LocalStart and LocalEnd must bracket zero for the baseline grid"

if ok:
    if not global_names:
        global_names = ["g_{:02d}".format(i) for i in range(len(global_starts))]
    elif len(global_names) != len(global_starts):
        ok = False
        status = "GlobalNames length must match GlobalStarts/GlobalEnds"


# --- Initialize / reset persistent state ------------------------------

state = sc.sticky.get(STATE_KEY)
if state is None or Reset:
    state = {
        "global_names": [],
        "global_samples": [],
        "local_names": [],
        "local_variants": [],
        "local_cell_count": 0,
        "samples_per_family": 0,
        "index": 0,
        "done": False,
        "sig": None,
    }

if ok:
    local_names = build_local_names(local_grid_n)
    sig = (
        tuple(global_names),
        tuple(global_starts),
        tuple(global_ends),
        n_global_families,
        local_grid_n,
        local_start,
        local_end,
        samples_per_family,
        seed,
    )

    if state["sig"] != sig:
        rng_global = random.Random(seed)
        rng_local = random.Random(seed + 1)

        global_samples = [
            [
                rng_global.uniform(global_starts[j], global_ends[j])
                for j in range(len(global_names))
            ]
            for _ in range(n_global_families)
        ]

        local_cell_count = local_grid_n * local_grid_n
        local_variants = []
        for _ in range(n_global_families):
            family_variants = [
                [
                    rng_local.uniform(local_start, local_end)
                    for _ in range(local_cell_count)
                ]
                for _ in range(n_local_variants)
            ]
            local_variants.append(family_variants)

        total_samples = n_global_families * samples_per_family

        state.update(
            {
                "global_names": list(global_names),
                "global_samples": global_samples,
                "local_names": local_names,
                "local_variants": local_variants,
                "local_cell_count": local_cell_count,
                "samples_per_family": samples_per_family,
                "index": 0,
                "done": (total_samples == 0),
                "sig": sig,
            }
        )


# --- Default outputs --------------------------------------------------

SampleId = None
GlobalFamilyId = None
LocalVariantId = None
GlobalVals = []
LocalGridVals = []
Done = False
Status = status


# --- Main logic -------------------------------------------------------

if ok:
    total_samples = len(state["global_samples"]) * state["samples_per_family"]
    idx = int(state["index"])

    if total_samples == 0:
        Done = True
        Status = "Done (no samples to emit)"
        sc.sticky[CASE_KEY] = None
        sc.sticky[ACTIVE_CASE_KEY] = CASE_KEY
    else:
        if idx >= total_samples:
            idx = total_samples - 1
            state["index"] = idx
            state["done"] = True

        case = build_case(state, idx)

        SampleId = case["sample_id"]
        GlobalFamilyId = case["global_family_id"]
        LocalVariantId = case["local_variant_id"]
        GlobalVals = list(case["global"]["vals"])
        LocalGridVals = list(case["local_grid"]["vals"])

        sc.sticky[CASE_KEY] = case
        sc.sticky[ACTIVE_CASE_KEY] = CASE_KEY

        if Run and not state["done"]:
            nxt = idx + 1
            if nxt >= total_samples:
                state["done"] = True
                state["index"] = total_samples - 1
            else:
                state["index"] = nxt

        Done = bool(state["done"])
        sample_kind = "baseline" if LocalVariantId == -1 else "variant"
        Status = "Sample {}/{} ({})".format(SampleId + 1, total_samples, sample_kind)

else:
    sc.sticky[CASE_KEY] = None
    sc.sticky[ACTIVE_CASE_KEY] = CASE_KEY

sc.sticky[STATE_KEY] = state
print("Status: ", Status)
