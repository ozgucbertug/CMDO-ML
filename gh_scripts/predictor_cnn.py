#! python 3
# venv: cmdo-ml-gh
# r: numpy==1.26.4, tensorflow==2.16.2
#
# ================================================================
# CNN REGRESSION PREDICTOR
# ----------------------------------------------------------------
# Loads the saved `.keras` CNN regressor and metadata from the
# provided artifacts folder, then predicts `max_disp` for one
# Grasshopper image sample at a time.
#
# HOW IT WORKS
#   1. Load model and metadata once and cache them in sc.sticky
#   2. Check that the incoming ImageArray matches the saved image shape
#   3. Normalize the image using the saved metadata rules
#   4. Run the Keras model and return the predicted max displacement
#
# INPUTS
#   ImageArray   (list[list[int]]) - One grayscale image sample
#   ArtifactsDir (str)             - Folder containing the saved artifacts
#   Run          (bool)            - Trigger prediction
#   Reset        (bool)            - Clear cached artifacts and reload next run
#
# OUTPUTS
#   YPred        (float/None)      - Predicted max displacement
#
# Ozguc Bertug Capunaman - CMDO - Spring 2026
# ================================================================

import json
import os

import numpy as np
import scriptcontext as sc
from tensorflow import keras


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


def to_plain_nested_list(v):
    """Recursively convert nested iterables to plain Python lists."""
    if isinstance(v, np.ndarray):
        return v.tolist()
    if isinstance(v, (str, bytes)):
        return v
    try:
        items = list(v)
    except TypeError:
        return v
    return [to_plain_nested_list(item) for item in items]


# --- Load / cache artifacts -----------------------------------------

def load_bundle(artifacts_dir):
    """Load model and metadata from disk."""
    model_path = os.path.join(artifacts_dir, "maxDisplacement_cnn_regressor.keras")
    metadata_path = os.path.join(artifacts_dir, "maxDisplacement_cnn_regressor_metadata.json")

    missing = [p for p in [model_path, metadata_path] if not os.path.exists(p)]
    if missing:
        raise IOError("Missing artifact(s): " + ", ".join(missing))

    with open(metadata_path, "r") as f:
        metadata = json.load(f)

    model = keras.models.load_model(model_path, compile=False)

    image_shape = tuple(int(v) for v in metadata.get("image_shape", []))
    if not image_shape:
        input_shape = model.input_shape
        if isinstance(input_shape, list):
            input_shape = input_shape[0]
        image_shape = tuple(int(v) for v in input_shape[1:] if v is not None)

    if len(image_shape) not in (2, 3):
        raise ValueError("Metadata does not contain a valid image_shape")

    return {
        "artifacts_dir": artifacts_dir,
        "model": model,
        "metadata": metadata,
        "image_shape": image_shape,
        "normalization": str(metadata.get("normalization", "")).strip().lower(),
    }


def get_bundle():
    """Return cached artifacts, reloading only when needed."""
    cache_key = "cnn_regression_predictor_bundle"
    artifacts_dir_raw = str(ArtifactsDir or "").strip()

    if not artifacts_dir_raw:
        raise ValueError("ArtifactsDir is required")

    artifacts_dir = os.path.abspath(os.path.normpath(os.path.expandvars(artifacts_dir_raw)))
    bundle = sc.sticky.get(cache_key)
    if Reset:
        bundle = None

    if bundle is None or bundle.get("artifacts_dir") != artifacts_dir:
        bundle = load_bundle(artifacts_dir)
        sc.sticky[cache_key] = bundle

    return bundle


# --- Build image input ----------------------------------------------

def build_image_input(image_array, image_shape, normalization):
    """Return one image tensor in the same shape used during training."""
    raw = to_plain_nested_list(image_array)
    try:
        x_img = np.asarray(raw, dtype="float32")
    except Exception:
        raise ValueError("ImageArray must be a rectangular numeric array")

    if x_img.size == 0:
        raise ValueError("ImageArray is empty")

    if len(image_shape) == 2:
        expected_hw = tuple(image_shape)
        expected_shape = tuple(image_shape)
    else:
        expected_hw = tuple(image_shape[:2])
        expected_shape = tuple(image_shape)

    if x_img.ndim == 2:
        if x_img.shape != expected_hw:
            raise ValueError(
                "Expected ImageArray shape {}, received {}".format(expected_hw, tuple(x_img.shape))
            )
        if len(expected_shape) == 3:
            if expected_shape[2] != 1:
                raise ValueError("Only single-channel images are supported by this predictor")
            x_img = x_img[:, :, np.newaxis]

    elif x_img.ndim == 3:
        if x_img.shape != expected_shape:
            raise ValueError(
                "Expected ImageArray shape {}, received {}".format(expected_shape, tuple(x_img.shape))
            )

    elif x_img.ndim == 4:
        if x_img.shape[0] != 1 or tuple(x_img.shape[1:]) != expected_shape:
            raise ValueError(
                "Expected batched image shape (1, {}), received {}".format(
                    expected_shape, tuple(x_img.shape)
                )
            )
        x_img = x_img[0]

    else:
        raise ValueError("ImageArray must be a 2D grayscale array or a single 3D image tensor")

    if normalization in ("", "none"):
        pass
    elif normalization == "divide_by_255":
        x_img = x_img / 255.0
    else:
        raise ValueError("Unsupported normalization in metadata: " + normalization)

    return np.expand_dims(x_img.astype("float32"), axis=0)


# --- Default outputs -------------------------------------------------

YPred = None


# --- Main logic ------------------------------------------------------

try:
    bundle = get_bundle()

    if Run:
        x_img = build_image_input(ImageArray, bundle["image_shape"], bundle["normalization"])
        y_pred = bundle["model"].predict(x_img, verbose=0)

        YPred = float(np.asarray(y_pred).reshape(-1)[0])

except Exception as e:
    raise RuntimeError(str(e))
