"""Circle-circle overlap detection for plant spacing warnings.

Per user decision: overlap percentage = overlap_area / area of the SMALLER
circle. Immediate-conflict warnings compare current diameters; the future
(>30%) warning compares expected mature diameters.
"""
import math

FUTURE_OVERLAP_THRESHOLD = 0.30


def circle_circle_overlap_area(c1, r1, c2, r2):
    """Area of intersection ("lens") between two circles."""
    d = math.hypot(c2[0] - c1[0], c2[1] - c1[1])
    if d >= r1 + r2:
        return 0.0
    if d <= abs(r1 - r2):
        return math.pi * min(r1, r2) ** 2

    r1_sq, r2_sq = r1 ** 2, r2 ** 2
    alpha = math.acos((d ** 2 + r1_sq - r2_sq) / (2 * d * r1))
    beta = math.acos((d ** 2 + r2_sq - r1_sq) / (2 * d * r2))
    return (
        r1_sq * (alpha - math.sin(2 * alpha) / 2)
        + r2_sq * (beta - math.sin(2 * beta) / 2)
    )


def overlap_fraction(c1, r1, c2, r2):
    """Overlap area as a fraction of the smaller circle's area."""
    smaller_area = math.pi * min(r1, r2) ** 2
    if smaller_area <= 0:
        return 0.0
    return circle_circle_overlap_area(c1, r1, c2, r2) / smaller_area


def immediate_conflict(c1, current_diameter1, c2, current_diameter2):
    """True if current footprints already overlap at all."""
    return overlap_fraction(c1, current_diameter1 / 2, c2, current_diameter2 / 2) > 0


def future_conflict(c1, expected_diameter1, c2, expected_diameter2):
    """True if expected mature footprints will overlap by more than 30%."""
    return (
        overlap_fraction(c1, expected_diameter1 / 2, c2, expected_diameter2 / 2)
        > FUTURE_OVERLAP_THRESHOLD
    )
