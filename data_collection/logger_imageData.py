# ================================================================
# IMAGE DATA LOGGER
# ----------------------------------------------------------------
# Converts 3D geometry into a grayscale heightmap PNG — one image
# per sample.  Each pixel's brightness encodes how high the geometry
# is at that point (black = ZMin, white = ZMax).  These images are
# the input data for a CNN (Convolutional Neural Network).
#
# HOW IT WORKS
#   1. A rectangle defines the region to scan (on the XY plane)
#   2. For each pixel, a ray is projected along the rectangle's
#      normal to find where it hits the geometry
#   3. The hit Z value is normalized to 0-255 and stored as a
#      grayscale pixel
#   4. The resulting image is saved as <Index>.png
#
# INPUTS
#   Geo       (geometry)     — Mesh, Surface, or Brep to rasterize
#   Rect      (Rectangle3d)  — Sampling region (typically on World XY)
#   W         (int)          — Image width in pixels  (e.g. 64, 128)
#   H         (int)          — Image height in pixels (e.g. 64, 128)
#   ZMin      (float)        — Z value that maps to black (0)
#   ZMax      (float)        — Z value that maps to white (255)
#   Directory (str)          — Output folder for the PNG files
#   Index     (int)          — Sample index (wire from Sampler)
#   Run       (bool)         — Trigger pulse to write one image
#   Reset     (bool)         — Allow re-writing the same Index
#
# OUTPUTS
#   PathOut   (str)          — Full path of the written PNG
#   Status    (str)          — Human-readable status message
#
# Ozguc Bertug Capunaman · CMDO · Spring 2026
# ================================================================

import os
import rhinoscriptsyntax as rs
import scriptcontext as sc

import System
from System.Drawing import Bitmap, Color
from System.Drawing.Imaging import ImageFormat

# --- Helpers ---------------------------------------------------------

def clamp01(t):
    """Clamp a value to the 0-1 range."""
    if t < 0.0: return 0.0
    if t > 1.0: return 1.0
    return t


def as_list(v):
    """Ensure v is a plain Python list (handles None, scalars, tuples)."""
    if v is None:
        return []
    return list(v) if isinstance(v, (list, tuple)) else [v]

# --- Initialize / reset persistent state ----------------------------

state = sc.sticky.get("heightmap_logger_state")
if state is None or Reset:
    state = {"last_index": None}

PathOut = ""
Status  = ""

# --- Guard checks (exit early if anything is missing) ----------------

ok = True

if not Run:
    Status = "Idle (Run is False)"
    ok = False

if ok and Index is None:
    Status = "Index is None"
    ok = False

if ok and state["last_index"] == int(Index):
    Status = "Index unchanged — nothing written"
    ok = False

if ok and Rect is None:
    Status = "Rect is None"
    ok = False

if ok and (W is None or H is None or int(W) <= 0 or int(H) <= 0):
    Status = "Invalid image dimensions (W / H)"
    ok = False

directory = (Directory or "").strip() if ok else ""
if ok and not directory:
    Status = "Directory is empty"
    ok = False

# --- Classify geometry -----------------------------------------------

if ok:
    directory = os.path.normpath(os.path.expandvars(directory))
    os.makedirs(directory, exist_ok=True)

    geo_ids  = as_list(Geo)
    mesh_ids = []
    srf_ids  = []
    for gid in geo_ids:
        if gid and rs.IsObject(gid):
            if rs.IsMesh(gid):
                mesh_ids.append(gid)
            elif rs.IsSurface(gid) or rs.IsPolysurface(gid):
                srf_ids.append(gid)

    if not mesh_ids and not srf_ids:
        Status = "Geo must contain mesh/surface/polysurface objects"
        ok = False

# --- Rasterize geometry into a heightmap image -----------------------

if ok:
    # Rectangle corners define our UV coordinate system
    p0 = Rect.Corner(0)            # Origin corner
    vx = Rect.Corner(1) - p0       # U direction (width)
    vy = Rect.Corner(3) - p0       # V direction (height)

    w = int(W)
    h = int(H)

    zmin = float(ZMin)
    zmax = float(ZMax)
    if zmax == zmin:
        zmax = zmin + 1e-6         # Avoid division by zero

    # Project along the rectangle's normal (straight down if rect is on XY)
    n = Rect.Plane.ZAxis
    dir_vec = (n.X, n.Y, n.Z)

    bmp = Bitmap(w, h)

    # Walk a grid of pixels; u and v go from 0 to 1 across the rectangle
    for row in range(h):
        v = (row + 0.5) / float(h)
        for col in range(w):
            u = (col + 0.5) / float(w)

            # 3D point on the rectangle corresponding to this pixel
            pt     = p0 + vx * u + vy * v
            pt_tup = (pt.X, pt.Y, pt.Z)

            # Project the point onto the geometry to find the hit Z
            hit = None
            if mesh_ids:
                proj = rs.ProjectPointToMesh([pt_tup], mesh_ids, dir_vec)
                if proj and len(proj) > 0:
                    hit = proj[0]
            if hit is None and srf_ids:
                proj = rs.ProjectPointToSurface([pt_tup], srf_ids, dir_vec)
                if proj and len(proj) > 0:
                    hit = proj[0]

            # Map hit Z to a 0-255 grayscale value
            if hit is not None:
                t = clamp01((float(hit[2]) - zmin) / (zmax - zmin))
                g = int(round(t * 255.0))
            else:
                g = 0  # No hit = black

            # Flip row: image row 0 is the top, but geometry Y increases upward
            bmp.SetPixel(col, h - 1 - row, Color.FromArgb(g, g, g))

    # Save and release the bitmap
    out_path = os.path.join(directory, f"{int(Index):06d}.png")
    bmp.Save(out_path, ImageFormat.Png)
    bmp.Dispose()

    PathOut = out_path
    Status  = "Wrote heightmap: " + out_path
    state["last_index"] = int(Index)

sc.sticky["heightmap_logger_state"] = state