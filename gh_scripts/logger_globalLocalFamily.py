# ================================================================
# GLOBAL + LOCAL FAMILY LOGGER
# ----------------------------------------------------------------
# Writes one structured inverse-design row per sample by reading the
# current case emitted by sampler_globalLocalFamilyGrid.py from
# sc.sticky. The logger keeps per-family baseline max_disp values so
# each local variant row can include max_disp_baseline and
# max_disp_delta.
#
# INPUTS
#   SampleId       (int)        - Current sample id from the sampler
#   Ys             (list/value) - Analysis outputs for this sample
#   YNames         (list[str])  - Column names for Ys
#   Directory      (str)        - Folder to save the CSV in
#   FileName       (str)        - CSV file name (default "global_local_family.csv")
#   Run            (bool)       - Trigger pulse to log one row
#   Reset          (bool)       - Clear state so next write starts a fresh file
#
# OUTPUTS
#   Count          (int)        - Number of rows written in the current file
#   LastRow        (dict)       - Most recently written row
#   LastSampleId   (int/None)   - Sample id of the most recently written row
#   Status         (str)        - Human-readable status message
#
# Ozguc Bertug Capunaman - CMDO - Spring 2026
# ================================================================

import csv
import os

import scriptcontext as sc


# --- Sticky keys ------------------------------------------------------

STICKY_PREFIX = "global_local_family"
ACTIVE_CASE_KEY = STICKY_PREFIX + "_active_case_key"
CASE_KEY_PREFIX = STICKY_PREFIX + "_case"

instance_suffix = ""
if "ghenv" in globals():
    instance_suffix = "_{}".format(ghenv.Component.InstanceGuid)

STATE_KEY = "global_local_family_logger_state" + instance_suffix


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


def normalize_names(values, names, prefix):
    """Return names aligned with values, falling back to numbered names."""
    raw_names = [str(v).strip() for v in as_list(names)]
    if len(raw_names) != len(values) or any(not name for name in raw_names):
        return ["{}_{:02d}".format(prefix, i) for i in range(len(values))]
    return raw_names


def find_duplicate_names(names):
    """Return duplicate names while preserving first-seen order."""
    seen = set()
    duplicates = []
    for name in names:
        if name in seen and name not in duplicates:
            duplicates.append(name)
        seen.add(name)
    return duplicates


def get_case(case_sample_id):
    """Load the active case object emitted by the paired sampler."""
    candidate_keys = []
    active_key = sc.sticky.get(ACTIVE_CASE_KEY)
    if active_key:
        candidate_keys.append(active_key)

    for key in sc.sticky.keys():
        if str(key).startswith(CASE_KEY_PREFIX) and key not in candidate_keys:
            candidate_keys.append(key)

    matches = []
    for key in candidate_keys:
        case = sc.sticky.get(key)
        if not isinstance(case, dict):
            continue
        if case_sample_id is None or int(case.get("sample_id", -1)) == int(case_sample_id):
            matches.append(case)

    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        raise RuntimeError("Multiple sampler cases match SampleId {}".format(case_sample_id))
    if case_sample_id is None:
        raise RuntimeError("No active sampler case found in sc.sticky")
    raise RuntimeError("No sampler case found for SampleId {}".format(case_sample_id))


def parse_numeric(v):
    """Return a float when possible, else None."""
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def fresh_state(csv_path=""):
    """Return a fresh logger state dictionary."""
    return {
        "last_sample_id": None,
        "count": 0,
        "baseline_by_family": {},
        "header_sig": None,
        "csv_path": csv_path,
        "last_row": {},
    }


# --- Initialize / reset persistent state ------------------------------

state = sc.sticky.get(STATE_KEY)
if state is None or Reset:
    state = fresh_state()


# --- Normalize inputs -------------------------------------------------

status = "Idle (Run is False)"
directory = (Directory or "").strip()
file_name = (FileName or "global_local_family.csv").strip()
if not file_name.lower().endswith(".csv"):
    file_name += ".csv"

y_vals = as_list(Ys)
y_names = normalize_names(y_vals, YNames, "y")


# --- Default outputs --------------------------------------------------

Count = state["count"]
LastRow = dict(state.get("last_row", {}))
LastSampleId = state["last_sample_id"]
Status = status


# --- Main logic -------------------------------------------------------

if Run:
    if SampleId is None:
        Status = "SampleId is None"
    elif not directory:
        Status = "Directory is empty"
    else:
        try:
            sample_id = int(SampleId)
            case = get_case(sample_id)

            global_names = list(case.get("global", {}).get("names", []))
            global_vals = list(case.get("global", {}).get("vals", []))
            local_names = list(case.get("local_grid", {}).get("names", []))
            local_vals = list(case.get("local_grid", {}).get("vals", []))

            if len(global_names) != len(global_vals):
                raise RuntimeError("Sampler case global names/values are misaligned")
            if len(local_names) != len(local_vals):
                raise RuntimeError("Sampler case local names/values are misaligned")

            csv_path = os.path.normpath(os.path.join(os.path.expandvars(directory), file_name))
            os.makedirs(os.path.dirname(csv_path), exist_ok=True)

            header = [
                "sample_id",
                "global_family_id",
                "local_variant_id",
            ] + global_names + local_names + y_names + [
                "max_disp_baseline",
                "max_disp_delta",
            ]
            duplicate_names = find_duplicate_names(header)
            if duplicate_names:
                raise RuntimeError(
                    "Duplicate CSV column names: " + ", ".join(duplicate_names)
                )
            header_sig = tuple(header)

            if state["csv_path"] != csv_path:
                state = fresh_state(csv_path=csv_path)

            if state["header_sig"] is None:
                state["header_sig"] = header_sig
            elif state["header_sig"] != header_sig:
                state = fresh_state(csv_path=csv_path)
                state["header_sig"] = header_sig

            if sample_id == state["last_sample_id"]:
                Status = "SampleId unchanged - nothing written"
            else:
                local_variant_id = int(case.get("local_variant_id", -1))
                is_baseline = (local_variant_id == -1)
                row = {
                    "sample_id": sample_id,
                    "global_family_id": int(case.get("global_family_id", -1)),
                    "local_variant_id": local_variant_id,
                    "max_disp_baseline": "",
                    "max_disp_delta": "",
                }

                row.update(dict(zip(global_names, global_vals)))
                row.update(dict(zip(local_names, local_vals)))
                row.update(dict(zip(y_names, y_vals)))

                family_id = row["global_family_id"]
                max_disp_val = parse_numeric(row.get("max_disp"))

                if is_baseline:
                    state["baseline_by_family"][family_id] = max_disp_val
                    if max_disp_val is not None:
                        row["max_disp_baseline"] = max_disp_val
                        row["max_disp_delta"] = 0.0
                else:
                    baseline_val = state["baseline_by_family"].get(family_id)
                    if baseline_val is not None and max_disp_val is not None:
                        row["max_disp_baseline"] = baseline_val
                        row["max_disp_delta"] = max_disp_val - baseline_val

                mode = "w" if state["count"] == 0 else "a"
                file_exists = os.path.exists(csv_path)

                with open(csv_path, mode, newline="") as f:
                    writer = csv.DictWriter(f, fieldnames=header, extrasaction="ignore")
                    if mode == "w" or not file_exists:
                        writer.writeheader()
                    writer.writerow(row)

                state.update(
                    {
                        "last_sample_id": sample_id,
                        "count": state["count"] + 1,
                        "last_row": row,
                    }
                )

                Count = state["count"]
                LastRow = dict(row)
                LastSampleId = sample_id
                Status = "Wrote sample row: " + csv_path

        except Exception as e:
            Status = str(e)

sc.sticky[STATE_KEY] = state

Count = state["count"]
LastRow = dict(state.get("last_row", {}))
LastSampleId = state["last_sample_id"]
print("Status: ", Status)
