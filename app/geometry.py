"""Polygon containment/overlap tests shared by garden_outline_tool.py.

Used to keep a flowerbed outline fully inside its garden outline and to
stop flowerbed outlines from overlapping each other. Plain point/segment
math (no numpy) — polygons here are always small (a handful of vertices).
"""

_EPS = 1e-9


def _orientation(p, q, r):
    val = (q[1] - p[1]) * (r[0] - q[0]) - (q[0] - p[0]) * (r[1] - q[1])
    if abs(val) < _EPS:
        return 0
    return 1 if val > 0 else 2


def _on_segment(a, point, b):
    return (min(a[0], b[0]) - _EPS <= point[0] <= max(a[0], b[0]) + _EPS
            and min(a[1], b[1]) - _EPS <= point[1] <= max(a[1], b[1]) + _EPS)


def segments_touch_or_cross(p1, p2, p3, p4):
    """True if segments p1-p2 and p3-p4 intersect, including touching endpoints."""
    o1, o2 = _orientation(p1, p2, p3), _orientation(p1, p2, p4)
    o3, o4 = _orientation(p3, p4, p1), _orientation(p3, p4, p2)
    if o1 != o2 and o3 != o4:
        return True
    if o1 == 0 and _on_segment(p1, p3, p2):
        return True
    if o2 == 0 and _on_segment(p1, p4, p2):
        return True
    if o3 == 0 and _on_segment(p3, p1, p4):
        return True
    if o4 == 0 and _on_segment(p3, p2, p4):
        return True
    return False


def segments_cross(p1, p2, p3, p4):
    """True only for a proper transversal crossing (touching endpoints don't count)."""
    o1, o2 = _orientation(p1, p2, p3), _orientation(p1, p2, p4)
    o3, o4 = _orientation(p3, p4, p1), _orientation(p3, p4, p2)
    return o1 != 0 and o2 != 0 and o3 != 0 and o4 != 0 and o1 != o2 and o3 != o4


def point_in_polygon(point, polygon):
    """Boundary-inclusive point-in-polygon test (ray casting)."""
    n = len(polygon)
    for i in range(n):
        a, b = polygon[i], polygon[(i + 1) % n]
        if _orientation(a, point, b) == 0 and _on_segment(a, point, b):
            return True
    x, y = point
    inside = False
    j = n - 1
    for i in range(n):
        xi, yi = polygon[i]
        xj, yj = polygon[j]
        if (yi > y) != (yj > y):
            x_intersect = (xj - xi) * (y - yi) / (yj - yi) + xi
            if x < x_intersect:
                inside = not inside
        j = i
    return inside


def polygon_fully_inside(inner, outer):
    """True if every point of `inner` lies within (or on the boundary of) `outer`."""
    for vertex in inner:
        if not point_in_polygon(vertex, outer):
            return False
    n, m = len(inner), len(outer)
    for i in range(n):
        a, b = inner[i], inner[(i + 1) % n]
        for j in range(m):
            c, d = outer[j], outer[(j + 1) % m]
            if segments_cross(a, b, c, d):
                return False
    return True


def polygons_overlap(poly_a, poly_b):
    """True if the two polygons share any area (edges cross, or one contains the other)."""
    n, m = len(poly_a), len(poly_b)
    for i in range(n):
        a1, a2 = poly_a[i], poly_a[(i + 1) % n]
        for j in range(m):
            b1, b2 = poly_b[j], poly_b[(j + 1) % m]
            if segments_cross(a1, a2, b1, b2):
                return True
    if point_in_polygon(poly_a[0], poly_b):
        return True
    if point_in_polygon(poly_b[0], poly_a):
        return True
    return False
