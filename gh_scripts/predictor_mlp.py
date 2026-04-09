#! python 3
# venv: cmdo-ml-gh
# r: numpy==1.26.4, pandas==2.2.3, scikit-learn==1.5.2, tensorflow==2.16.2
#
# ================================================================
# MLP REGRESSION PREDICTOR
# ----------------------------------------------------------------
# Loads the saved `.keras` regressor, scaler, and metadata from
# `inclass_examples/artifacts/mlp_regression`, then predicts
# `max_disp` for one Grasshopper sample at a time.
#
# HOW IT WORKS
#   1. Load model/scaler/metadata once and cache them in sc.sticky
#   2. Check that the incoming X values match the saved feature count
#   3. Scale X with the saved scaler
#   4. Run the Keras model and return the predicted max displacement
#
# INPUTS
#   XVals        (list[float])      - Feature values for one sample
#   XNames       (list[str]/None)   - Optional feature names for XVals
#   ArtifactsDir (str)              - Folder containing the saved artifacts
#   Run          (bool)             - Trigger prediction
#   Reset        (bool)             - Clear cached artifacts and reload next run
#
# OUTPUTS
#   YPred        (float/None)  - Predicted max displacement
#
# Ozguc Bertug Capunaman - CMDO - Spring 2026
# ================================================================

import json
import os
import pickle

import numpy as np
import pandas as pd
import scriptcontext as sc
from tensorflow import keras


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


def load_bundle(artifacts_dir):
    """Load model, scaler, and metadata from disk."""
    model_path = os.path.join(artifacts_dir, "maxDisplacement_regressor.keras")
    scaler_path = os.path.join(artifacts_dir, "maxDisplacement_regressor_scaler.pkl")
    metadata_path = os.path.join(artifacts_dir, "maxDisplacement_regressor_metadata.json")

    missing = [p for p in [model_path, scaler_path, metadata_path] if not os.path.exists(p)]
    if missing:
        raise IOError("Missing artifact(s): " + ", ".join(missing))

    with open(scaler_path, "rb") as f:
        scaler = pickle.load(f)

    with open(metadata_path, "r") as f:
        metadata = json.load(f)

    model = keras.models.load_model(model_path, compile=False)
    feature_cols = list(metadata.get("feature_cols", []))

    if not feature_cols:
        raise ValueError("Metadata does not contain feature_cols")

    return {
        "artifacts_dir": artifacts_dir,
        "model": model,
        "scaler": scaler,
        "metadata": metadata,
        "feature_cols": feature_cols,
    }


def get_bundle():
    """Return cached artifacts, reloading only when needed."""
    cache_key = "mlp_regression_predictor_bundle"
    artifacts_dir = os.path.abspath((ArtifactsDir or "").strip())

    if not artifacts_dir:
        raise ValueError("ArtifactsDir is required")

    bundle = sc.sticky.get(cache_key)
    if Reset:
        bundle = None

    if bundle is None or bundle.get("artifacts_dir") != artifacts_dir:
        bundle = load_bundle(artifacts_dir)
        sc.sticky[cache_key] = bundle

    return bundle


def build_feature_input(x_vals, x_names, feature_cols):
    """Return one feature row, optionally aligned by incoming feature names."""
    if len(x_vals) != len(feature_cols):
        raise ValueError(
            "Expected {} input values, received {}".format(len(feature_cols), len(x_vals))
        )

    if not x_names:
        return np.array([x_vals], dtype=float)

    if len(x_names) != len(x_vals):
        raise ValueError(
            "Expected {} XNames, received {}".format(len(x_vals), len(x_names))
        )

    value_by_name = dict(zip(x_names, x_vals))
    missing = [name for name in feature_cols if name not in value_by_name]
    extra = [name for name in x_names if name not in feature_cols]

    if missing:
        raise ValueError("Missing named input(s): " + ", ".join(missing))
    if extra:
        raise ValueError("Unexpected XNames input(s): " + ", ".join(extra))

    ordered_vals = [value_by_name[name] for name in feature_cols]
    return pd.DataFrame([ordered_vals], columns=feature_cols)


YPred = None

try:
    bundle = get_bundle()

    if Run:
        x_vals = [float(v) for v in as_list(XVals)]
        x_names = [str(v) for v in as_list(globals().get("XNames")) if str(v).strip()]

        x_row = build_feature_input(x_vals, x_names, bundle["feature_cols"])
        x_scaled = bundle["scaler"].transform(x_row)
        y_pred = bundle["model"].predict(x_scaled, verbose=0)

        YPred = float(np.asarray(y_pred).reshape(-1)[0])

except Exception as e:
    raise RuntimeError(str(e))
