"""Garden/bed outline primitives: rectangle, circle, quarter-circle, polygon.

Each shape knows how to compute its own "critical dimension" label and its
area, and exposes drag handles for freehand refinement. Units here are
screen pixels treated as abstract "garden units" — no real-world scale
conversion is implemented at this layer.

Rectangle/Circle/QuarterCircle exist for loading older garden saves; new
garden and bed outlines are always drawn as a Polygon via
garden_outline_tool.py, which converts its pixel dimensions to meters using
its own pixels_per_meter scale.
"""
import math

ORIENTATIONS = ("top-left", "top-right", "bottom-right", "bottom-left")


class Rectangle:
    shape_type = "rectangle"

    def __init__(self, x1, y1, x2, y2):
        self.x1, self.y1, self.x2, self.y2 = x1, y1, x2, y2

    def _normalized(self):
        x1, x2 = sorted((self.x1, self.x2))
        y1, y2 = sorted((self.y1, self.y2))
        return x1, y1, x2, y2

    @property
    def width(self):
        x1, _, x2, _ = self._normalized()
        return x2 - x1

    @property
    def height(self):
        _, y1, _, y2 = self._normalized()
        return y2 - y1

    def dimension_label(self):
        return f"{self.width:.0f} x {self.height:.0f} units"

    def area(self):
        return self.width * self.height

    def handles(self):
        x1, y1, x2, y2 = self._normalized()
        return [(x1, y1), (x2, y1), (x2, y2), (x1, y2)]

    def move_handle(self, index, pos):
        # Opposite corner stays fixed; dragged handle becomes the new corner.
        opposite = self.handles()[(index + 2) % 4]
        self.x1, self.y1 = opposite
        self.x2, self.y2 = pos

    def polygon_points(self):
        return self.handles()

    def to_dict(self):
        return {"type": self.shape_type, "x1": self.x1, "y1": self.y1, "x2": self.x2, "y2": self.y2}

    @classmethod
    def from_dict(cls, d):
        return cls(d["x1"], d["y1"], d["x2"], d["y2"])


class Circle:
    shape_type = "circle"

    def __init__(self, cx, cy, radius):
        self.cx, self.cy, self.radius = cx, cy, radius

    def dimension_label(self):
        return f"Radius: {self.radius:.0f} units"

    def area(self):
        return math.pi * self.radius ** 2

    def handles(self):
        # Center (move handle) + one edge handle (resize handle).
        return [(self.cx, self.cy), (self.cx + self.radius, self.cy)]

    def move_handle(self, index, pos):
        if index == 0:
            self.cx, self.cy = pos
        else:
            self.radius = max(5.0, math.hypot(pos[0] - self.cx, pos[1] - self.cy))

    def polygon_points(self, segments=32):
        return [
            (
                self.cx + self.radius * math.cos(2 * math.pi * i / segments),
                self.cy + self.radius * math.sin(2 * math.pi * i / segments),
            )
            for i in range(segments)
        ]

    def to_dict(self):
        return {"type": self.shape_type, "cx": self.cx, "cy": self.cy, "radius": self.radius}

    @classmethod
    def from_dict(cls, d):
        return cls(d["cx"], d["cy"], d["radius"])


class QuarterCircle:
    shape_type = "quarter_circle"

    def __init__(self, cx, cy, radius, orientation="top-left"):
        self.cx, self.cy, self.radius = cx, cy, radius
        self.orientation = orientation

    def dimension_label(self):
        return f"Radius: {self.radius:.0f} units ({self.orientation})"

    def area(self):
        return math.pi * self.radius ** 2 / 4

    def cycle_orientation(self):
        idx = ORIENTATIONS.index(self.orientation)
        self.orientation = ORIENTATIONS[(idx + 1) % len(ORIENTATIONS)]

    def handles(self):
        return [(self.cx, self.cy), (self.cx + self.radius, self.cy)]

    def move_handle(self, index, pos):
        if index == 0:
            self.cx, self.cy = pos
        else:
            self.radius = max(5.0, math.hypot(pos[0] - self.cx, pos[1] - self.cy))

    def _angle_range(self):
        return {
            "top-left": (180, 270),
            "top-right": (270, 360),
            "bottom-right": (0, 90),
            "bottom-left": (90, 180),
        }[self.orientation]

    def polygon_points(self, segments=16):
        start, end = self._angle_range()
        points = [(self.cx, self.cy)]
        for i in range(segments + 1):
            angle = math.radians(start + (end - start) * i / segments)
            points.append((self.cx + self.radius * math.cos(angle), self.cy + self.radius * math.sin(angle)))
        return points

    def to_dict(self):
        return {
            "type": self.shape_type,
            "cx": self.cx,
            "cy": self.cy,
            "radius": self.radius,
            "orientation": self.orientation,
        }

    @classmethod
    def from_dict(cls, d):
        return cls(d["cx"], d["cy"], d["radius"], d.get("orientation", "top-left"))


class Polygon:
    shape_type = "polygon"

    def __init__(self, vertices):
        self.vertices = list(vertices)

    def dimension_label(self):
        xs = [v[0] for v in self.vertices]
        ys = [v[1] for v in self.vertices]
        width = max(xs) - min(xs)
        height = max(ys) - min(ys)
        return f"{width:.0f} x {height:.0f} units (bounding box)"

    def area(self):
        # Shoelace formula.
        n = len(self.vertices)
        if n < 3:
            return 0.0
        total = 0.0
        for i in range(n):
            x1, y1 = self.vertices[i]
            x2, y2 = self.vertices[(i + 1) % n]
            total += x1 * y2 - x2 * y1
        return abs(total) / 2

    def handles(self):
        return list(self.vertices)

    def move_handle(self, index, pos):
        self.vertices[index] = pos

    def polygon_points(self):
        return list(self.vertices)

    def to_dict(self):
        return {"type": self.shape_type, "vertices": [list(v) for v in self.vertices]}

    @classmethod
    def from_dict(cls, d):
        return cls([tuple(v) for v in d["vertices"]])


_SHAPE_CLASSES = {cls.shape_type: cls for cls in (Rectangle, Circle, QuarterCircle, Polygon)}


def shape_from_dict(d):
    return _SHAPE_CLASSES[d["type"]].from_dict(d)
