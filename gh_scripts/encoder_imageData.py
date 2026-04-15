# ================================================================
# IMAGE DATA ENCODER
# ----------------------------------------------------------------
# Converts 3D geometry into a grayscale heightmap array using the
# same pixel values and orientation as logger_imageData.py.
#
# HOW IT WORKS
#   1. A rectangle defines the region to scan (on the XY plane)
#   2. For each pixel, a ray is projected along the rectangle's
#      normal to find where it hits the geometry
#   3. The hit Z value is normalized to 0-255 and stored as a
#      grayscale value
#   4. The result is returned as a 2D Python list instead of a PNG
#
# This teaching example assumes the geometry behaves like a simple
# height field: one valid hit per pixel, with no overhangs or
# undercuts along the projection direction.
#
# INPUTS
#   Geo        (geometry)    - Mesh, Surface, or Brep to rasterize
#                              from Grasshopper or referenced Rhino geometry
#   Rect       (Rectangle3d) - Sampling region (typically on World XY)
#   W          (int)         - Image width in pixels (e.g. 64, 128)
#   H          (int)         - Image height in pixels (e.g. 64, 128)
#   ZMin       (float)       - Z value that maps to black (0)
#   ZMax       (float)       - Z value that maps to white (255)
#   Run        (bool)        - Trigger to build the image array
#
# OUTPUTS
#   ImageArray (list[list[int]]) - 2D grayscale array matching the logger PNG
#   Status     (str)             - Human-readable status message
#
# Ozguc Bertug Capunaman - CMDO - Spring 2026
# ================================================================

import Rhino
import rhinoscriptsyntax as rs


# --- Helpers ---------------------------------------------------------

def clamp01(t):
    """Clamp a value to the 0-1 range."""
    if t < 0.0:
        return 0.0
    if t > 1.0:
        return 1.0
    return t


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


# --- Normalize inputs ------------------------------------------------

ok = True
w = None
h = None
zmin = None
zmax = None
status = ""

if not Run:
    status = "Idle (Run is False)"
    ok = False

if ok and Rect is None:
    status = "Rect is None"
    ok = False

if ok:
    try:
        w = int(W)
        h = int(H)
    except (TypeError, ValueError):
        status = "Invalid image dimensions (W / H)"
        ok = False

if ok and (w <= 0 or h <= 0):
    status = "Invalid image dimensions (W / H)"
    ok = False

if ok:
    try:
        zmin = float(ZMin)
        zmax = float(ZMax)
    except (TypeError, ValueError):
        status = "ZMin / ZMax must be numbers"
        ok = False


# --- Default outputs -------------------------------------------------

ImageArray = []
Status = status


# --- Main logic ------------------------------------------------------

if ok:
    meshes = []
    breps = []
    for item in as_list(Geo):
        geom = None

        if isinstance(item, Rhino.Geometry.Mesh):
            geom = item
        elif isinstance(item, Rhino.Geometry.Brep):
            geom = item
        elif isinstance(item, Rhino.Geometry.Surface):
            geom = item.ToBrep()
        else:
            try:
                if rs.IsObject(item):
                    geom = rs.coercegeometry(item)
                    if isinstance(geom, Rhino.Geometry.Surface):
                        geom = geom.ToBrep()
            except Exception:
                geom = None

        if isinstance(geom, Rhino.Geometry.Mesh):
            meshes.append(geom)
        elif isinstance(geom, Rhino.Geometry.Brep):
            breps.append(geom)

    if not meshes and not breps:
        Status = "Geo must contain mesh/surface/polysurface geometry"
        ok = False

if ok:
    # Rectangle corners define our UV coordinate system.
    p0 = Rect.Corner(0)
    vx = Rect.Corner(1) - p0
    vy = Rect.Corner(3) - p0

    if zmax == zmin:
        zmax = zmin + 1e-6

    # Project along the rectangle's normal (straight down if rect is on XY).
    n = Rect.Plane.ZAxis
    tol = Rhino.RhinoDoc.ActiveDoc.ModelAbsoluteTolerance if Rhino.RhinoDoc.ActiveDoc else 0.01

    ImageArray = [[0 for _ in range(w)] for _ in range(h)]

    for row in range(h):
        v = (row + 0.5) / float(h)
        image_row = h - 1 - row

        for col in range(w):
            u = (col + 0.5) / float(w)
            pt = p0 + vx * u + vy * v

            # We intentionally keep this simple for teaching: the input
            # geometry is assumed to have one valid hit per pixel.
            hit = None
            if meshes:
                proj = Rhino.Geometry.Intersect.Intersection.ProjectPointsToMeshes(
                    meshes, [pt], n, tol
                )
                if proj and len(proj) > 0:
                    hit = proj[0]
            if hit is None and breps:
                proj = Rhino.Geometry.Intersect.Intersection.ProjectPointsToBreps(
                    breps, [pt], n, tol
                )
                if proj and len(proj) > 0:
                    hit = proj[0]

            if hit is not None:
                t = clamp01((float(hit.Z) - zmin) / (zmax - zmin))
                g = int(round(t * 255.0))
            else:
                g = 0

            ImageArray[image_row][col] = g

    Status = "Built image array: {} x {}".format(h, w)

print("Status: ", Status)
